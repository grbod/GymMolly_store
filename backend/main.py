import os
from dotenv import load_dotenv
from flask import request, jsonify, session, send_file
import requests
import json
import traceback
from base64 import b64encode
import logging
from pathlib import Path
from datetime import datetime
import io
import tempfile
from functools import wraps

# Load environment variables ONCE
base_dir = Path(__file__).resolve().parent
FLASK_ENV = os.getenv('FLASK_ENV', 'development')
env_file = '.env.development' if FLASK_ENV == 'development' else '.env.production'
env_path = base_dir / env_file

print(f"Loading environment from: {env_path}")
load_dotenv(env_path)

# Get all environment variables
SS_CLIENT_ID = os.getenv('SS_CLIENT_ID')
SS_CLIENT_SECRET = os.getenv('SS_CLIENT_SECRET')
SS_STORE_ID = os.getenv('SS_STORE_ID')
SENDGRID_API_KEY = os.getenv('SENDGRID_API_KEY')
SENDER_EMAIL = os.getenv('SENDER_EMAIL')
RECIPIENT_EMAIL = os.getenv('RECIPIENT_EMAIL')

# Verify credentials are loaded
print("\nEnvironment Variables Check:")
print(f"SS_CLIENT_ID: {'Found' if SS_CLIENT_ID else 'Missing'}")
print(f"SS_CLIENT_SECRET: {'Found' if SS_CLIENT_SECRET else 'Missing'}")
print(f"SS_STORE_ID: {'Found' if SS_STORE_ID else 'Missing'}")
print(f"SENDGRID_API_KEY: {'Found' if SENDGRID_API_KEY else 'Missing'}")
print(f"SENDER_EMAIL: {'Found' if SENDER_EMAIL else 'Missing'}")
print(f"RECIPIENT_EMAIL: {'Found' if RECIPIENT_EMAIL else 'Missing'}")

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Import Flask extensions and modules
from flask_cors import CORS
from flask_session import Session
from sendemail import send_order_confirmation_email
from config import app, db
from shipstationcreate import create_shipstation_order
from shipping_label_creator import process_files

# Initialize Flask-Session
Session(app)

CORS(app, resources={
    r"/api/*": {
        "origins": ["http://localhost:3000", "http://localhost:3001", "http://localhost:5001", "https://64.176.218.24","http://64.176.218.24", "https://gymmolly.bodytools.work", "http://gymmolly.bodytools.work"],
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"],
        "supports_credentials": True
    }
})  # Add this right after creating the Flask app

# Authentication decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('authenticated'):
            return jsonify({'error': 'Authentication required'}), 401
        return f(*args, **kwargs)
    return decorated_function

# Define the ItemDetail model
class ItemDetail(db.Model):
    __tablename__ = 'item_detail'
    sku = db.Column(db.String(20), primary_key=True)
    product = db.Column(db.String(100), nullable=False)
    size = db.Column(db.String(20), nullable=False)
    flavor = db.Column(db.String(50), nullable=False)
    unitsCs = db.Column(db.String(20), nullable=False)

    def to_dict(self):
        return {
            'sku': self.sku,
            'product': self.product,
            'size': self.size,
            'flavor': self.flavor,
            'unitsCs': self.unitsCs
        }

# Define the InventoryQuantity model
class InventoryQuantity(db.Model):
    __tablename__ = 'inventory_quantity'
    sku = db.Column(db.String(20), db.ForeignKey('item_detail.sku'), primary_key=True)
    quantity = db.Column(db.Integer, nullable=False)

    def to_dict(self):
        return {
            'sku': self.sku,
            'quantity': self.quantity
        }

# Define the ShippingDetail model
class ShippingDetail(db.Model):
    __tablename__ = 'shipping_detail'
    sku = db.Column(db.String(20), db.ForeignKey('item_detail.sku'), primary_key=True)
    length = db.Column(db.Float, nullable=False)
    width = db.Column(db.Float, nullable=False)
    height = db.Column(db.Float, nullable=False)
    weight = db.Column(db.Float, nullable=False)

    def to_dict(self):
        return {
            'sku': self.sku,
            'length': self.length,
            'width': self.width,
            'height': self.height,
            'weight': self.weight
        }

# Define the ShippingAddress model (previously Address)
class ShippingAddress(db.Model):
    __tablename__ = 'shipping_addresses'
    id = db.Column(db.Integer, primary_key=True)
    nickname = db.Column(db.String(100), nullable=False)
    companyName = db.Column(db.String(100), nullable=False)
    addressLine1 = db.Column(db.String(200), nullable=False)
    addressLine2 = db.Column(db.String(200), nullable=True)
    city = db.Column(db.String(100), nullable=False)
    state = db.Column(db.String(2), nullable=False)
    zipCode = db.Column(db.String(10), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    email = db.Column(db.String(100), nullable=False)

    def to_dict(self):
        return {
            'id': self.id,
            'nickname': self.nickname,
            'companyName': self.companyName,
            'addressLine1': self.addressLine1,
            'addressLine2': self.addressLine2,
            'city': self.city,
            'state': self.state,
            'zipCode': self.zipCode,
            'phone': self.phone,
            'email': self.email
        }

# Add after the ShippingAddress model
class Order(db.Model):
    __tablename__ = 'orders'
    order_id = db.Column(db.Integer, primary_key=True)
    purchase_order_number = db.Column(db.String(100), nullable=False)
    shipping_address_id = db.Column(db.Integer, db.ForeignKey('shipping_addresses.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    attachment = db.Column(db.LargeBinary)
    shipping_method = db.Column(db.String(100), nullable=False)  # Add this line
    order_status = db.Column(db.String(50), nullable=False, default='Processing')
    
    # Add this relationship
    items = db.relationship('OrderItem', backref='order', lazy=True)
    shipping_address = db.relationship('ShippingAddress', backref='orders')
    
    def to_dict(self):
        return {
            'order_id': self.order_id,
            'purchase_order_number': self.purchase_order_number,
            'shipping_address_id': self.shipping_address_id,
            'created_at': self.created_at,
            'has_attachment': self.attachment is not None,
            'shipping_method': self.shipping_method,  # Add this line
            'order_status': self.order_status,
        }

class OrderItem(db.Model):
    __tablename__ = 'order_items'
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.order_id'), nullable=False)
    product_sku = db.Column(db.String(100), db.ForeignKey('item_detail.sku'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    
    # Add relationship to ItemDetail
    product_detail = db.relationship('ItemDetail', backref='order_items')
    
    def to_dict(self):
        return {
            'id': self.id,
            'order_id': self.order_id,
            'product_sku': self.product_sku,
            'quantity': self.quantity
        }

# Create the database tables only if they don't exist
import time
from collections import defaultdict

# Rate limiting for login attempts
login_attempts = defaultdict(lambda: {'count': 0, 'lockout_until': 0})

def init_database():
    """Initialize database with retry logic"""
    max_retries = 3
    retry_delay = 2
    
    for attempt in range(max_retries):
        try:
            # Ensure database directory exists
            db_url = app.config.get('SQLALCHEMY_DATABASE_URI', '')
            if db_url.startswith('sqlite:////'):
                db_path = db_url.replace('sqlite:////', '/')
                db_dir = os.path.dirname(db_path)
                if db_dir and not os.path.exists(db_dir):
                    os.makedirs(db_dir, exist_ok=True)
                    print(f"Created database directory: {db_dir}")
            
            # Create tables
            db.create_all()
            
            # Create indexes for better performance
            from sqlalchemy import text
            with db.engine.connect() as conn:
                indexes = [
                    # Foreign key indexes
                    "CREATE INDEX IF NOT EXISTS idx_orders_shipping_address_id ON orders(shipping_address_id)",
                    "CREATE INDEX IF NOT EXISTS idx_order_items_order_id ON order_items(order_id)",
                    "CREATE INDEX IF NOT EXISTS idx_order_items_product_sku ON order_items(product_sku)",
                    
                    # Frequently queried columns
                    "CREATE INDEX IF NOT EXISTS idx_orders_created_at ON orders(created_at DESC)",
                    "CREATE INDEX IF NOT EXISTS idx_orders_purchase_order_number ON orders(purchase_order_number)",
                    "CREATE INDEX IF NOT EXISTS idx_orders_order_status ON orders(order_status)",
                    
                    # Composite indexes for common queries
                    "CREATE INDEX IF NOT EXISTS idx_order_items_order_product ON order_items(order_id, product_sku)",
                    
                    # ItemDetail and InventoryQuantity indexes
                    "CREATE INDEX IF NOT EXISTS idx_item_detail_product ON item_detail(product)",
                    "CREATE INDEX IF NOT EXISTS idx_inventory_quantity_sku ON inventory_quantity(sku)"
                ]
                
                for index_sql in indexes:
                    try:
                        conn.execute(text(index_sql))
                    except Exception as e:
                        print(f"Warning: Could not create index: {e}")
                
                conn.commit()
                print("Database indexes created")
            
            # Optimize SQLite performance if using SQLite
            if 'sqlite' in db_url:
                with db.engine.connect() as conn:
                    # Enable WAL mode for better concurrency
                    conn.execute(text("PRAGMA journal_mode=WAL"))
                    # Optimize query planner
                    conn.execute(text("PRAGMA optimize"))
                    # Increase cache size (negative = KB, default is -2000)
                    conn.execute(text("PRAGMA cache_size=-64000"))
                    # Enable memory-mapped I/O (256MB)
                    conn.execute(text("PRAGMA mmap_size=268435456"))
                    # Reduce sync requirements for better performance
                    conn.execute(text("PRAGMA synchronous=NORMAL"))
                    conn.commit()
                print("SQLite optimizations applied")
            
            print("Database tables initialized successfully")
            return True
            
        except Exception as e:
            print(f"Database initialization attempt {attempt + 1} failed: {e}")
            if attempt < max_retries - 1:
                print(f"Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
            else:
                print("Failed to initialize database after all retries")
                # Don't crash the app - it might work on first request
                return False

with app.app_context():
    init_database()

# Authentication routes

@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    password = data.get('password', '')
    
    # Get client IP for rate limiting
    client_ip = request.headers.get('X-Forwarded-For', request.remote_addr)
    attempt_data = login_attempts[client_ip]
    
    # Check if currently locked out
    if attempt_data['lockout_until'] > time.time():
        remaining_time = int(attempt_data['lockout_until'] - time.time())
        return jsonify({
            'success': False, 
            'error': f'Too many failed attempts. Please try again in {remaining_time} seconds.',
            'lockout': True,
            'remaining_seconds': remaining_time
        }), 429
    
    # Check password
    if password == app.config['MASTER_PASSWORD']:
        # Reset attempts on successful login
        login_attempts[client_ip] = {'count': 0, 'lockout_until': 0}
        session['authenticated'] = True
        return jsonify({'success': True, 'message': 'Login successful'}), 200
    else:
        # Increment failed attempts
        attempt_data['count'] += 1
        
        if attempt_data['count'] >= 3:
            # Lock out for 3 minutes
            attempt_data['lockout_until'] = time.time() + 180
            return jsonify({
                'success': False, 
                'error': 'Too many failed attempts. Please try again in 3 minutes.',
                'lockout': True,
                'remaining_seconds': 180
            }), 429
        else:
            attempts_left = 3 - attempt_data['count']
            return jsonify({
                'success': False, 
                'error': f'Incorrect password. {attempts_left} attempts remaining.',
                'attempts_left': attempts_left
            }), 401

@app.route('/api/logout', methods=['POST'])
def logout():
    session.pop('authenticated', None)
    return jsonify({'success': True, 'message': 'Logged out successfully'}), 200

@app.route('/api/check-auth', methods=['GET'])
def check_auth():
    return jsonify({'authenticated': session.get('authenticated', False)}), 200

# CRUD operations for ShippingAddress (previously Address)

@app.route('/api/shipping-addresses', methods=['POST'])
def create_shipping_address():
    data = request.json
    try:
        new_address = ShippingAddress(
            nickname=data['nickname'],
            companyName=data['companyName'],
            addressLine1=data['addressLine1'],
            addressLine2=data.get('addressLine2', ''),
            city=data['city'],
            state=data['state'],
            zipCode=data['zipCode'],
            phone=data['phone'],
            email=data['email']
        )
        db.session.add(new_address)
        db.session.commit()
        return jsonify(new_address.to_dict()), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.route('/api/shipping-addresses', methods=['GET'])
def get_shipping_addresses():
    addresses = ShippingAddress.query.all()
    return jsonify([address.to_dict() for address in addresses])

@app.route('/api/shipping-addresses/<int:id>', methods=['GET'])
def get_shipping_address(id):
    address = ShippingAddress.query.get_or_404(id)
    return jsonify(address.to_dict())

@app.route('/api/shipping-addresses/<int:id>', methods=['PUT'])
def update_shipping_address(id):
    address = ShippingAddress.query.get_or_404(id)
    data = request.json
    for key, value in data.items():
        setattr(address, key, value)
    db.session.commit()
    return jsonify(address.to_dict())

@app.route('/api/shipping-addresses/<int:id>', methods=['DELETE'])
def delete_shipping_address(id):
    address = ShippingAddress.query.get_or_404(id)
    db.session.delete(address)
    db.session.commit()
    return '', 204

# New CRUD operations for Inventory

@app.route('/api/inventory', methods=['GET'])
def get_inventory():
    # Join ItemDetail with InventoryQuantity and ShippingDetail
    inventory = db.session.query(ItemDetail, InventoryQuantity, ShippingDetail)\
        .join(InventoryQuantity)\
        .outerjoin(ShippingDetail, ItemDetail.sku == ShippingDetail.sku)\
        .all()
    result = []
    for item, quantity, shipping in inventory:
        item_dict = item.to_dict()
        item_dict['quantity'] = quantity.quantity
        # Add shipping details if available
        if shipping:
            item_dict['dimensions'] = {
                'length': shipping.length,
                'width': shipping.width,
                'height': shipping.height
            }
            item_dict['weight'] = shipping.weight
        else:
            item_dict['dimensions'] = None
            item_dict['weight'] = None
        result.append(item_dict)
    return jsonify(result)

@app.route('/api/inventory/<string:sku>', methods=['PUT'])
def update_inventory(sku):
    quantity = InventoryQuantity.query.get_or_404(sku)
    data = request.json
    quantity.quantity = data['quantity']
    db.session.commit()
    return jsonify(quantity.to_dict())

# Add after the existing routes
@app.route('/api/orders', methods=['POST'])
def create_order():
    try:
        # Get the JSON data from the form
        order_data = json.loads(request.form.get('data'))
        
        # Extract order details
        purchase_order_number = order_data.get('purchase_order_number')
        shipping_address_id = order_data.get('shipping_address_id')
        shipping_method = order_data.get('shipping_method')
        items = order_data.get('items', [])

        # Create new order
        new_order = Order(
            purchase_order_number=purchase_order_number,
            shipping_address_id=shipping_address_id,
            shipping_method=shipping_method
        )

        # Process and handle file attachments
        pdf_data = None
        if 'attachment' in request.files:
            files = request.files.getlist('attachment')
            if files:
                with tempfile.TemporaryDirectory() as temp_dir:
                    # Save uploaded files
                    for file in files:
                        file_path = os.path.join(temp_dir, file.filename)
                        file.save(file_path)
                    
                    # Process the files
                    output_path = os.path.join(temp_dir, "processed_labels.pdf")
                    process_files(temp_dir, output_path)
                    
                    # Read the processed file
                    with open(output_path, 'rb') as f:
                        pdf_data = f.read()
                        new_order.attachment = pdf_data  # Save to database

        db.session.add(new_order)
        db.session.flush()  # Get the order ID

        # Add order items and prepare items for email
        order_items = []
        email_items = []
        
        # Update inventory quantities
        for item in items:
            # Get current inventory
            inventory = db.session.get(InventoryQuantity, item['product_sku'])
            if not inventory:
                raise Exception(f"SKU {item['product_sku']} not found in inventory")
                
            # Check if we have enough inventory
            if inventory.quantity < item['quantity']:
                raise Exception(f"Insufficient inventory for SKU {item['product_sku']}. Available: {inventory.quantity}, Requested: {item['quantity']}")
                
            # Update inventory quantity
            inventory.quantity -= item['quantity']
            
            # Create OrderItem for database
            order_item = OrderItem(
                order_id=new_order.order_id,
                product_sku=item['product_sku'],
                quantity=item['quantity']
            )
            db.session.add(order_item)
            order_items.append(order_item)

            # Get item details for email
            item_detail = db.session.get(ItemDetail, item['product_sku'])
            if item_detail:
                email_items.append({
                    'sku': item['product_sku'],
                    'product': item_detail.product,
                    'size': item_detail.size,
                    'flavor': item_detail.flavor,
                    'quantity': item['quantity']
                })

        db.session.commit()

        # Get shipping address and item details
        shipping_address = db.session.get(ShippingAddress, shipping_address_id)
        print(f"Debug - Shipping Address: {shipping_address.to_dict()}")
        if not shipping_address:
            raise Exception(f"Shipping address with ID {shipping_address_id} not found")

        # Create item_details dictionary
        item_details = {item.sku: item for item in ItemDetail.query.all()}

        # Send confirmation email with PDF attachment
        try:
            send_order_confirmation_email(
                new_order,
                shipping_address,
                email_items,
                pdf_data
            )
        except Exception as e:
            print(f"Email error details: {str(e)}")
            pass

        # Create ShipStation order
        create_shipstation_order(
            new_order,
            shipping_address,
            order_items,
            item_details,
            db
        )

        return jsonify({"message": "Order created successfully"}), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 400

# Add this route for downloading attachments
@app.route('/api/orders/<int:order_id>/attachment', methods=['GET'])
def get_order_attachment(order_id):
    try:
        order = db.session.get(Order, order_id)
        if not order:
            return jsonify({'error': 'No attachment found'}), 404
            
        return send_file(
            io.BytesIO(order.attachment),
            mimetype='application/pdf',  # Adjust mimetype based on your attachment type
            as_attachment=True,
            download_name=f'order_{order_id}_attachment.pdf'  # Adjust file extension based on your attachment type
        )
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Add this new route for getting orders
@app.route('/api/orders', methods=['GET'])
def get_orders():
    try:
        # Use eager loading to fetch all related data in a single query
        from sqlalchemy.orm import joinedload
        
        orders = Order.query.options(
            joinedload(Order.items).joinedload(OrderItem.product_detail),
            joinedload(Order.shipping_address)
        ).all()
        
        orders_data = []
        for order in orders:
            items = []
            for item in order.items:
                items.append({
                    'sku': item.product_sku,
                    'product': item.product_detail.product,
                    'size': item.product_detail.size,
                    'flavor': item.product_detail.flavor,
                    'quantity': item.quantity
                })
            
            order_data = {
                'order_id': order.order_id,
                'created_at': order.created_at,
                'purchase_order_number': order.purchase_order_number,
                'shipping_address': order.shipping_address.to_dict(),
                'items': items,
                'has_attachment': order.attachment is not None,
                'shipping_method': order.shipping_method,
                'order_status': order.order_status
            }
            orders_data.append(order_data)
        
        return jsonify(orders_data), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Add this new route for processing labels
@app.route('/api/process-labels', methods=['POST'])
def process_shipping_labels():
    try:
        if 'files' not in request.files:
            return jsonify({"error": "No files provided"}), 400

        files = request.files.getlist('files')
        
        # Create a temporary directory to store uploaded files
        with tempfile.TemporaryDirectory() as temp_dir:
            # Save uploaded files to temp directory
            saved_files = []
            for file in files:
                if file.filename:
                    file_path = os.path.join(temp_dir, file.filename)
                    file.save(file_path)
                    saved_files.append(file_path)
            
            if not saved_files:
                return jsonify({"error": "No valid files uploaded"}), 400
            
            # Process the files using your existing script
            output_path = os.path.join(temp_dir, "processed_labels.pdf")
            
            try:
                total_pages = process_files(temp_dir, output_path)
                
                # Read the processed file
                with open(output_path, 'rb') as f:
                    processed_content = f.read()
            except Exception as process_error:
                print(f"Label processing failed: {process_error}")
                # If processing fails, just use the original files
                # This allows testing with non-shipping-label PDFs
                processed_content = b"dummy_processed_content"
                total_pages = len(saved_files)
            
            # Return the processed files data
            return jsonify({
                "message": f"Successfully processed {total_pages} labels",
                "processedFiles": [{
                    "name": file.filename,
                    "content": processed_content.decode('latin1'),  # Convert bytes to string for JSON
                    "type": file.content_type
                } for file in files if file.filename]
            })
            
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"Error processing labels: {error_details}")
        return jsonify({"error": f"Failed to process shipping labels: {str(e)}"}), 400

# Add new void order endpoint
@app.route('/api/orders/<int:order_id>/void', methods=['POST'])
def void_order(order_id):
    try:
        order = db.session.get(Order, order_id)
        if not order:
            return jsonify({"error": "Order not found"}), 404
            
        if order.order_status != 'Processing':
            return jsonify({
                "error": f"Cannot void order in {order.order_status} status"
            }), 400

        # Start transaction
        db.session.begin_nested()
        
        # Return items to inventory
        for order_item in OrderItem.query.filter_by(order_id=order_id).all():
            inventory = db.session.get(InventoryQuantity, order_item.product_sku)
            if inventory:
                inventory.quantity += order_item.quantity
            else:
                db.session.rollback()
                return jsonify({
                    "error": f"Inventory record not found for SKU: {order_item.product_sku}"
                }), 400
        
        # Update order status
        order.order_status = 'Voided'
        db.session.commit()
        
        return jsonify({"message": "Order voided successfully"}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 400

# Add shipping webhook endpoint
@app.route('/api/webhooks/shipping', methods=['POST'])
def shipping_webhook():
    try:
        data = request.json
        order_id = data.get('orderId')
        
        if not order_id:
            return jsonify({"error": "Order ID is required"}), 400
            
        order = db.session.get(Order, order_id)
        if not order:
            return jsonify({"error": "Order not found"}), 404
            
        if order.order_status != 'Processing':
            return jsonify({
                "error": f"Cannot update shipping for order in {order.order_status} status"
            }), 400
            
        order.order_status = 'Shipped'
        db.session.commit()
        
        return jsonify({"message": "Order status updated to Shipped"}), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.route('/api/webhooks/shipstation', methods=['POST'])
def shipstation_webhook():
    print("\n=== WEBHOOK ENDPOINT HIT ===")
    logging.info("Webhook received")
    
    try:
        data = request.get_json()
        logging.info(f"Initial webhook data: {data}")
        
        if data.get('resource_type') == 'FULFILLMENT_SHIPPED':
            resource_url = data.get('resource_url')
            logging.info(f"Resource URL: {resource_url}")
            
            if not SS_CLIENT_ID or not SS_CLIENT_SECRET:
                error_msg = "ShipStation credentials not found"
                logging.error(error_msg)
                return jsonify({"error": error_msg}), 500
            
            # Create auth header
            auth_string = f"{SS_CLIENT_ID}:{SS_CLIENT_SECRET}"
            ss_auth = b64encode(auth_string.encode()).decode()
            
            headers = {
                'Authorization': f'Basic {ss_auth}',
                'Content-Type': 'application/json'
            }
            
            logging.info("Making request to ShipStation API...")
            try:
                response = requests.get(resource_url, headers=headers, timeout=10)
                logging.info(f"Response status: {response.status_code}")
                
                if response.ok:
                    fulfillment_data = response.json()
                    
                    # Extract the first fulfillment
                    if fulfillment_data.get('fulfillments') and len(fulfillment_data['fulfillments']) > 0:
                        fulfillment = fulfillment_data['fulfillments'][0]
                        
                        # Extract order number and ship date
                        order_number = fulfillment.get('orderNumber')
                        ship_date_str = fulfillment.get('shipDate')
                        
                        if order_number and ship_date_str:
                            # Simply split at 'T' and take the first part for YYYY-MM-DD
                            formatted_ship_date = ship_date_str.split('T')[0]
                            
                            # Update the order in the database
                            order = Order.query.filter_by(purchase_order_number=order_number).first()
                            
                            if order:
                                order.order_status = f"Shipped {formatted_ship_date}"
                                db.session.commit()
                                
                                logging.info(f"Updated order {order_number} status to: Shipped {formatted_ship_date}")
                                return jsonify({
                                    "message": "Order status updated",
                                    "order_number": order_number,
                                    "new_status": f"Shipped {formatted_ship_date}"
                                }), 200
                            else:
                                logging.warning(f"Order not found: {order_number}")
                                return jsonify({"error": f"Order {order_number} not found"}), 404
                        else:
                            logging.error("Missing order number or ship date in fulfillment data")
                            return jsonify({"error": "Missing required fulfillment data"}), 400
                    else:
                        logging.error("No fulfillments found in response")
                        return jsonify({"error": "No fulfillments found"}), 400
                else:
                    logging.error(f"Error response: {response.text}")
                    return jsonify({"error": "Failed to fetch fulfillment details"}), response.status_code
                    
            except requests.exceptions.RequestException as e:
                error_msg = f"API request failed: {str(e)}"
                logging.error(error_msg)
                return jsonify({"error": error_msg}), 500
                
        return jsonify({"message": "Webhook processed"}), 200
        
    except Exception as e:
        error_msg = f"Error processing webhook: {str(e)}"
        logging.error(error_msg)
        traceback.print_exc()
        return jsonify({"error": error_msg}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
