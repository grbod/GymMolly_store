from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

# SendGrid configuration
SENDGRID_API_KEY = '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'
SENDER_EMAIL = 'customerservice@bodynutrition.com'
RECIPIENT_EMAIL = 'greg@bodynutrition.com'

def send_order_confirmation_email(order, address, items):
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
                {address.companyName}<br>
                {address.addressLine1}<br>
                {address.addressLine2 + '<br>' if address.addressLine2 else ''}
                {address.city}, {address.state} {address.zipCode}<br>
                Phone: {address.phone}<br>
                Email: {address.email}
            </p>
            
            <h3>Ordered Items:</h3>
            {items_table}
            
            <p><strong>Attachment:</strong> {' Yes' if order.attachment else ' No'}</p>
            
            <p><strong>Shipping Method:</strong> {order.shipping_method}</p>
        </body>
    </html>
    """

    message = Mail(
        from_email=SENDER_EMAIL,
        to_emails=RECIPIENT_EMAIL,
        subject=f'New Order Received - PO#{order.purchase_order_number}',
        html_content=html_content
    )

    try:
        sg = SendGridAPIClient(SENDGRID_API_KEY)
        response = sg.send(message)
        print(f"Order confirmation email sent. Status code: {response.status_code}")
        return True
    except Exception as e:
        print(f"Error sending email: {str(e)}")
        return False
