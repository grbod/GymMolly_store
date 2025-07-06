from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import (
    Mail, Attachment, FileContent, FileName,
    FileType, Disposition, ContentId
)
import base64
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Get environment variables
SENDGRID_API_KEY = os.getenv('SENDGRID_API_KEY')
SENDER_EMAIL = os.getenv('SENDER_EMAIL')
RECIPIENT_EMAIL = os.getenv('RECIPIENT_EMAIL')

def send_order_confirmation_email(order, shipping_address, items, pdf_data=None, zip_data=None):
    try:
        # Add debug logging
        print(f"Attempting to send email with SendGrid API key: {SENDGRID_API_KEY[:10]}...")
        print(f"From: {SENDER_EMAIL}")
        print(f"Shipping Address Email: {shipping_address.email}")
        print(f"Recipient Email: {RECIPIENT_EMAIL}")
        
        if not SENDGRID_API_KEY:
            raise ValueError("SendGrid API key is missing")
        
        # Add size check for PDF (SendGrid has a 30MB limit)
        if pdf_data and len(pdf_data) > 30_000_000:  # 30MB in bytes
            print("PDF too large for email attachment")
            pdf_data = None  # Don't attach if too large

        sg = SendGridAPIClient(SENDGRID_API_KEY)
        
        # Define recipients
        admin_emails = RECIPIENT_EMAIL.split(',') if RECIPIENT_EMAIL else []  # Split the comma-separated emails
        to_emails = admin_emails.copy()  # Start with admin emails
        
        if shipping_address.email:  # Add customer email if it exists
            to_emails.append(shipping_address.email)
        
        # Create email message
        message = Mail(
            from_email=SENDER_EMAIL,
            to_emails=to_emails,
            subject=f'Order Confirmation - PO #{order.purchase_order_number}',
            html_content=create_email_content(order, shipping_address, items)
        )

        # Add PDF attachment if provided
        if pdf_data:
            try:
                # Convert binary PDF data to base64
                encoded_pdf = base64.b64encode(pdf_data).decode()
                
                # Create attachment
                attachment = Attachment()
                attachment.file_content = FileContent(encoded_pdf)
                attachment.file_type = FileType('application/pdf')
                attachment.file_name = FileName(f'shipping_labels_PO_{order.purchase_order_number}.pdf')
                attachment.disposition = Disposition('attachment')
                attachment.content_id = ContentId('Shipping Labels')
                
                # Add attachment to email
                message.add_attachment(attachment)  # Changed from message.attachment = attachment
            except Exception as e:
                print(f"Error processing attachment: {str(e)}")
                # Continue without attachment if there's an error

        # Add ZIP attachment if provided
        if zip_data:
            try:
                # Convert binary ZIP data to base64
                encoded_zip = base64.b64encode(zip_data).decode()
                
                # Create ZIP attachment
                zip_attachment = Attachment()
                zip_attachment.file_content = FileContent(encoded_zip)
                zip_attachment.file_type = FileType('application/zip')
                zip_attachment.file_name = FileName(f'original_labels_PO_{order.purchase_order_number}.zip')
                zip_attachment.disposition = Disposition('attachment')
                zip_attachment.content_id = ContentId('Original Labels')
                
                # Add ZIP attachment to email
                message.add_attachment(zip_attachment)
            except Exception as e:
                print(f"Error processing ZIP attachment: {str(e)}")
                # Continue without ZIP attachment if there's an error

        try:
            response = sg.send(message)
            print(f'Email sent successfully. Status code: {response.status_code}')
            print(f'Response headers: {response.headers}')
            return True
        except Exception as e:
            print(f'SendGrid API error: {str(e)}')
            if hasattr(e, 'body'):
                print(f'Error body: {e.body}')
            raise

    except Exception as e:
        print(f'Error sending email: {str(e)}')
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
