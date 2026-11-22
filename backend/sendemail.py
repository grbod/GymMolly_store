import base64
import logging
import os

import requests
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

logger = logging.getLogger(__name__)

CLOUDFLARE_API_BASE = 'https://api.cloudflare.com/client/v4'
ATTACHMENT_TIMEOUT_SECONDS = 120
PLAIN_TIMEOUT_SECONDS = 30

# Cloudflare caps the whole message at 25 MiB including base64 overhead (~4/3).
# 18 MiB of raw attachments is about 24 MiB encoded, leaving room for headers and body.
MAX_ATTACHMENT_BYTES = 18 * 1024 * 1024
MAX_ATTACHMENT_MIB = 18


def _env(name):
    return os.getenv(name) or ''


def use_cloudflare():
    """Cloudflare when both vars are set, otherwise the SendGrid rollback path."""
    return bool(_env('CLOUDFLARE_ACCOUNT_ID') and _env('CLOUDFLARE_EMAIL_API_TOKEN'))


def budget_attachments(attachments, max_bytes=MAX_ATTACHMENT_BYTES):
    """Apply one whole-message budget to the combined raw attachment bytes.

    attachments: list of (filename, mime_type, bytes); falsy data entries are ignored.
    Attachments are kept in order while the running total stays at or under max_bytes;
    any that would push the total over are omitted.
    Returns (kept, omitted_filenames).
    """
    kept, omitted, total = [], [], 0
    for filename, mime, data in attachments:
        if not data:
            continue
        if total + len(data) <= max_bytes:
            kept.append((filename, mime, data))
            total += len(data)
        else:
            omitted.append(filename)
    return kept, omitted


def _normalize(addr):
    return addr.strip().lower()


def _send_cloudflare(to_emails, sender, subject, html, attachments):
    account_id = _env('CLOUDFLARE_ACCOUNT_ID')
    token = _env('CLOUDFLARE_EMAIL_API_TOKEN')
    url = f"{CLOUDFLARE_API_BASE}/accounts/{account_id}/email/sending/send"
    body = {'to': to_emails, 'from': sender, 'subject': subject, 'html': html}
    if attachments:
        body['attachments'] = [
            {
                'content': base64.b64encode(data).decode('ascii'),
                'filename': filename,
                'type': mime,
                'disposition': 'attachment',
            }
            for filename, mime, data in attachments
        ]
    timeout = ATTACHMENT_TIMEOUT_SECONDS if attachments else PLAIN_TIMEOUT_SECONDS

    def clean(text):
        # Never let the token reach a log line, even through an exception message.
        return str(text).replace(token, '[redacted]')[:300]

    try:
        resp = requests.post(
            url,
            headers={'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'},
            json=body,
            timeout=timeout,
        )
    except requests.Timeout:
        logger.error('Cloudflare email send timed out after %ss', timeout)
        return False
    except requests.RequestException as e:
        logger.error('Cloudflare email send failed: %s', clean(type(e).__name__))
        return False

    try:
        payload = resp.json()
        if not isinstance(payload, dict):
            raise ValueError('not an object')
    except ValueError:
        logger.error('Cloudflare email send failed: HTTP %s, malformed response body', resp.status_code)
        return False

    result = payload.get('result')
    result = result if isinstance(result, dict) else {}
    message_id = result.get('message_id')

    if not (200 <= resp.status_code < 300) or payload.get('success') is not True:
        errors = payload.get('errors') if isinstance(payload.get('errors'), list) else []
        codes = ','.join(str(e.get('code', '?')) for e in errors if isinstance(e, dict)) or 'none'
        msgs = '; '.join(clean(e.get('message', '')) for e in errors if isinstance(e, dict))
        logger.error('Cloudflare email send failed: HTTP %s, error codes %s, %s', resp.status_code, codes, msgs)
        return False

    accepted = set()
    for key in ('delivered', 'queued'):
        values = result.get(key)
        if isinstance(values, list):
            accepted.update(_normalize(v) for v in values if isinstance(v, str))
    missing = [a for a in to_emails if _normalize(a) not in accepted]
    if missing:
        logger.error(
            'Cloudflare email send incomplete: HTTP %s, message_id %s, %d of %d recipients not delivered or queued',
            resp.status_code, message_id, len(missing), len(to_emails),
        )
        return False

    logger.info('Cloudflare email sent: HTTP %s, message_id %s', resp.status_code, message_id)
    return True


def _send_sendgrid(to_emails, sender, subject, html, attachments):
    # Rollback path. Imported lazily so Cloudflare-only deployments do not need the SDK.
    from sendgrid import SendGridAPIClient
    from sendgrid.helpers.mail import (
        Mail, Attachment, FileContent, FileName, FileType, Disposition
    )

    api_key = _env('SENDGRID_API_KEY')
    if not api_key:
        logger.error('No email provider configured (set Cloudflare vars or SENDGRID_API_KEY)')
        return False
    try:
        message = Mail(from_email=sender, to_emails=to_emails, subject=subject, html_content=html)
        for filename, mime, data in attachments:
            message.add_attachment(Attachment(
                file_content=FileContent(base64.b64encode(data).decode()),
                file_name=FileName(filename),
                file_type=FileType(mime),
                disposition=Disposition('attachment'),
            ))
        response = SendGridAPIClient(api_key).send(message)
        ok = response.status_code in (200, 201, 202)
        logger.info('SendGrid email send: HTTP %s', response.status_code)
        return ok
    except Exception as e:
        logger.error('SendGrid email send failed: %s', type(e).__name__)
        return False


def send_email(to_emails, subject, html, attachments=None, sender=None):
    """Single send point for all GymMolly email. Returns True only on confirmed success.

    attachments: list of (filename, mime_type, bytes). The whole-message size budget is
    enforced here too; an over-budget message is refused rather than sent partially.
    """
    sender = sender or _env('SENDER_EMAIL')
    seen, recipients = set(), []
    for addr in to_emails or []:
        if addr and _normalize(addr) not in seen:
            seen.add(_normalize(addr))
            recipients.append(addr.strip())
    if not recipients or not sender:
        logger.error('Email not sent: missing recipients or sender')
        return False

    attachments = [(f, m, d) for f, m, d in (attachments or []) if d]
    if sum(len(d) for _, _, d in attachments) > MAX_ATTACHMENT_BYTES:
        logger.error('Email not sent: attachments exceed the %d MiB budget', MAX_ATTACHMENT_MIB)
        return False

    if use_cloudflare():
        return _send_cloudflare(recipients, sender, subject, html, attachments)
    return _send_sendgrid(recipients, sender, subject, html, attachments)


def send_order_confirmation_email(order, shipping_address, items, pdf_data=None, zip_data=None):
    try:
        po = order.purchase_order_number
        candidates = [
            (f'shipping_labels_PO_{po}.pdf', 'application/pdf', pdf_data),
            (f'original_labels_PO_{po}.zip', 'application/zip', zip_data),
        ]
        attachments, omitted = budget_attachments(candidates)
        if omitted:
            logger.warning(
                'PO %s: omitted attachments over the %d MiB combined limit: %s',
                po, MAX_ATTACHMENT_MIB, ', '.join(omitted),
            )

        recipient_email = _env('RECIPIENT_EMAIL')
        to_emails = [a.strip() for a in recipient_email.split(',') if a.strip()]
        if shipping_address.email:
            to_emails.append(shipping_address.email)

        html = create_email_content(order, shipping_address, items)
        if omitted:
            note = (
                f'<p style="color: #b00020;"><strong>Attachment omitted:</strong> '
                f'{", ".join(omitted)} not attached because the combined attachments exceed '
                f'the {MAX_ATTACHMENT_MIB} MB email limit. Please retrieve the label files separately.</p>'
            )
            html = html.replace('</body>', note + '</body>', 1)

        return send_email(
            to_emails,
            f'Order Confirmation - PO #{po}',
            html,
            attachments,
        )
    except Exception as e:
        logger.error('Error sending order confirmation email: %s', type(e).__name__)
        return False

def create_email_content(order, shipping_address, items):
    # Create the order details table in HTML
    items_table = """
    <table style="border-collapse: collapse; width: 600px; margin: 5pt 0;">
        <tr style="background-color: #f8f9fa;">
            <th style="border: 1px solid #dee2e6; padding: 5pt; width: 30%;">SKU</th>
            <th style="border: 1px solid #dee2e6; padding: 5pt; width: 25%;">Product</th>
            <th style="border: 1px solid #dee2e6; padding: 5pt; width: 10%;">Size</th>
            <th style="border: 1px solid #dee2e6; padding: 5pt; width: 20%;">Flavor</th>
            <th style="border: 1px solid #dee2e6; padding: 5pt; width: 15%;">Cases</th>
        </tr>
    """
    
    for item in items:
        items_table += f"""
        <tr>
            <td style="border: 1px solid #dee2e6; padding: 5pt; width: 30%;">{item['sku']}</td>
            <td style="border: 1px solid #dee2e6; padding: 5pt; width: 25%;">{item['product']}</td>
            <td style="border: 1px solid #dee2e6; padding: 5pt; width: 10%;">{item['size']}</td>
            <td style="border: 1px solid #dee2e6; padding: 5pt; width: 20%;">{item['flavor']}</td>
            <td style="border: 1px solid #dee2e6; padding: 5pt; width: 15%;">{item['quantity']}</td>
        </tr>
        """
    
    items_table += "</table>"

    # Create the email content
    html_content = f"""
    <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <h2>New Order Received</h2>
            
            <h3>Order Details:</h3>
            <p><strong>Purchase Order Number:</strong> {order.purchase_order_number}</p>
            <p><strong>Order Date:</strong> {order.created_at.strftime('%Y-%m-%d %H:%M:%S')}</p>
            
            <h3>Shipping Address:</h3>
            <p>
                {shipping_address.companyName}<br>
                {shipping_address.addressLine1}<br>
                {shipping_address.addressLine2 + '<br>' if shipping_address.addressLine2 else ''}
                {shipping_address.city}, {shipping_address.state} {shipping_address.zipCode}<br>
                Phone: {shipping_address.phone}<br>
                Email: {shipping_address.email}
            </p>
            
            <h3>Ordered Items:</h3>
            {items_table}
            
            <p><strong>Attachment:</strong> {' Yes' if order.attachment else ' No'}</p>
            
            <p><strong>Shipping Method:</strong> {order.shipping_method}</p>
        </body>
    </html>
    """

    return html_content
