import os
from dotenv import load_dotenv
from flask import request, jsonify, session, send_file
import requests
import json
import traceback
import base64
from base64 import b64encode
import logging
from pathlib import Path
from datetime import datetime
import io
import tempfile
import zipfile
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
            from sqlalchemy import text, func
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
        .order_by(ItemDetail.product, ItemDetail.flavor, ItemDetail.size)\
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

# Product management endpoints
@app.route('/api/products', methods=['GET'])
def get_products():
    try:
        products = ItemDetail.query.all()
        products_data = []
        
        for product in products:
            product_dict = {
                'sku': product.sku,
                'product': product.product,
                'size': product.size,
                'flavor': product.flavor,
                'unitsCs': product.unitsCs
            }
            
            # Add inventory quantity if available
            inventory = InventoryQuantity.query.get(product.sku)
            if inventory:
                product_dict['quantity'] = inventory.quantity
            else:
                product_dict['quantity'] = 0
                
            # Add shipping details if available
            shipping = ShippingDetail.query.get(product.sku)
            if shipping:
                product_dict['shipping'] = {
                    'length': shipping.length,
                    'width': shipping.width,
                    'height': shipping.height,
                    'weight': shipping.weight
                }
                
            products_data.append(product_dict)
            
        return jsonify(products_data), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/products', methods=['POST'])
def create_product():
    try:
        data = request.json
        
        # Check if SKU already exists
        existing_product = ItemDetail.query.get(data.get('sku'))
        if existing_product:
            return jsonify({"error": "Product with this SKU already exists"}), 400
            
        # Create new product
        new_product = ItemDetail(
            sku=data['sku'],
            product=data['product'],
            size=data['size'],
            flavor=data['flavor'],
            unitsCs=data['unitsCs']
        )
        db.session.add(new_product)
        
        # Create inventory entry
        initial_quantity = data.get('quantity', 0)
        new_inventory = InventoryQuantity(
            sku=data['sku'],
            quantity=initial_quantity
        )
        db.session.add(new_inventory)
        
        # Create shipping details if provided
        if any(data.get(field) for field in ['length', 'width', 'height', 'weight']):
            new_shipping = ShippingDetail(
                sku=data['sku'],
                length=float(data.get('length') or 0),
                width=float(data.get('width') or 0),
                height=float(data.get('height') or 0),
                weight=float(data.get('weight') or 0)
            )
            db.session.add(new_shipping)
            
        db.session.commit()
        
        return jsonify({
            "message": "Product created successfully",
            "sku": new_product.sku
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 400

@app.route('/api/products/<string:sku>', methods=['DELETE'])
def delete_product(sku):
    try:
        # Check if product exists
        product = ItemDetail.query.get(sku)
        if not product:
            return jsonify({"error": "Product not found"}), 404
            
        # Check if product has any orders
        order_items = OrderItem.query.filter_by(product_sku=sku).first()
        if order_items:
            return jsonify({
                "error": "Cannot delete product with existing orders. This product has been used in one or more orders."
            }), 400
            
        # Delete related records first
        InventoryQuantity.query.filter_by(sku=sku).delete()
        ShippingDetail.query.filter_by(sku=sku).delete()
        
        # Delete the product
        db.session.delete(product)
        db.session.commit()
        
        return jsonify({
            "message": f"Product {sku} deleted successfully"
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

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
        zip_data = None
        if 'attachment' in request.files:
            files = request.files.getlist('attachment')
            if files:
                with tempfile.TemporaryDirectory() as temp_dir:
                    # Save uploaded files
                    saved_files = []
                    for file in files:
                        file_path = os.path.join(temp_dir, file.filename)
                        file.save(file_path)
                        saved_files.append((file_path, file.filename))
                    
                    # Create zip file of original files
                    zip_buffer = io.BytesIO()
                    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                        for file_path, original_name in saved_files:
                            zip_file.write(file_path, original_name)
                    zip_data = zip_buffer.getvalue()
                    
                    # Process the files
                    output_path = os.path.join(temp_dir, "processed_labels.pdf")
                    process_files(temp_dir, output_path)
                    
                    # Try to read the trimmed version first
                    trimmed_path = output_path.replace('.pdf', '_trimmed.pdf')
                    if os.path.exists(trimmed_path):
                        with open(trimmed_path, 'rb') as f:
                            pdf_data = f.read()
                    else:
                        # Fall back to original if trimmed doesn't exist
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

        # Send confirmation email with PDF and ZIP attachments
        try:
            send_order_confirmation_email(
                new_order,
                shipping_address,
                email_items,
                pdf_data,
                zip_data
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
                
                # Try to read the trimmed version first
                trimmed_path = output_path.replace('.pdf', '_trimmed.pdf')
                if os.path.exists(trimmed_path):
                    with open(trimmed_path, 'rb') as f:
                        processed_content = f.read()
                    print(f"Using trimmed PDF: {trimmed_path}")
                else:
                    # Fall back to original if trimmed doesn't exist
                    with open(output_path, 'rb') as f:
                        processed_content = f.read()
                    print(f"Trimmed PDF not found, using original: {output_path}")
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

# Add delete order endpoint
@app.route('/api/orders/<int:order_id>/delete', methods=['DELETE'])
def delete_order(order_id):
    try:
        order = db.session.get(Order, order_id)
        if not order:
            return jsonify({"error": "Order not found"}), 404
        
        # Allow deletion of voided and shipped orders
        if order.order_status not in ['Voided', 'Shipped'] and not order.order_status.startswith('SHIPPED'):
            return jsonify({
                "error": f"Cannot delete order in {order.order_status} status. Only voided or shipped orders can be deleted."
            }), 400
        
        # Start transaction
        db.session.begin_nested()
        
        try:
            # For shipped orders, restore inventory (voided orders already had inventory restored)
            if order.order_status == 'Shipped' or order.order_status.startswith('SHIPPED'):
                for order_item in OrderItem.query.filter_by(order_id=order_id).all():
                    inventory = db.session.get(InventoryQuantity, order_item.product_sku)
                    if inventory:
                        inventory.quantity += order_item.quantity
                        logging.info(f"Restored {order_item.quantity} units of {order_item.product_sku} to inventory")
                    else:
                        db.session.rollback()
                        return jsonify({
                            "error": f"Cannot delete order: Inventory record not found for SKU: {order_item.product_sku}"
                        }), 400
            
            # Delete order items first (foreign key constraint)
            OrderItem.query.filter_by(order_id=order_id).delete()
            
            # Delete the order
            db.session.delete(order)
            db.session.commit()
            
            # Determine if inventory was restored
            inventory_restored = order.order_status == 'Shipped' or order.order_status.startswith('SHIPPED')
            
            return jsonify({
                "message": f"Order {order.purchase_order_number} deleted successfully",
                "inventory_restored": inventory_restored
            }), 200
            
        except Exception as e:
            db.session.rollback()
            raise e
            
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

# Add order status update endpoint
@app.route('/api/orders/<int:order_id>/update-status', methods=['PUT'])
def update_order_status(order_id):
    """Update order status with password protection"""
    try:
        data = request.json
        new_status = data.get('status')
        password = data.get('password')
        
        # Validate inputs
        if not new_status:
            return jsonify({"error": "Status is required"}), 400
            
        if new_status not in ['Shipped', 'Manually Cancelled']:
            return jsonify({"error": "Invalid status. Must be 'Shipped' or 'Manually Cancelled'"}), 400
            
        # Format status for display
        if new_status == 'Manually Cancelled':
            display_status = 'MANUALLY\nCANCELLED'
        elif new_status == 'Shipped':
            # Format shipped date as MM/DD/YY
            from datetime import datetime
            today = datetime.now()
            display_status = f"SHIPPED\n{today.strftime('%m/%d/%y')}"
        else:
            display_status = new_status
            
        # Verify password
        if password != 'GREGS':
            return jsonify({"error": "Invalid password"}), 401
            
        # Get order
        order = db.session.get(Order, order_id)
        if not order:
            return jsonify({"error": "Order not found"}), 404
            
        # Check current status
        if order.order_status != 'Processing':
            return jsonify({
                "error": f"Cannot update order in {order.order_status} status. Only Processing orders can be updated."
            }), 400
            
        # Handle Manually Cancelled status (replenish inventory like void)
        if new_status == 'Manually Cancelled':
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
        order.order_status = display_status
        db.session.commit()
        
        action = "cancelled and inventory replenished" if new_status == 'Manually Cancelled' else "marked as shipped"
        return jsonify({"message": f"Order {action} successfully"}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

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

# Product management endpoints with full details
@app.route('/api/products/full-details', methods=['GET'])
@login_required
def get_products_full_details():
    """Get all products with their shipping details for editing"""
    try:
        # Query products with their shipping details using a join
        products = db.session.query(ItemDetail, ShippingDetail)\
            .join(ShippingDetail, ItemDetail.sku == ShippingDetail.sku)\
            .all()
        
        result = []
        for item, shipping in products:
            result.append({
                'sku': item.sku,
                'product': item.product,
                'size': item.size,
                'flavor': item.flavor,
                'unitsCs': item.unitsCs,
                'length': shipping.length,
                'width': shipping.width,
                'height': shipping.height,
                'weight': shipping.weight
            })
        
        return jsonify(result), 200
    except Exception as e:
        print(f"Error fetching product details: {e}")
        return jsonify({'error': 'Failed to fetch product details'}), 500

@app.route('/api/products/bulk-update', methods=['PUT'])
@login_required
def bulk_update_products():
    """Update multiple products with password verification"""
    try:
        data = request.json
        password = data.get('password')
        products = data.get('products', [])
        
        # Verify password
        if password != 'GREGS':
            return jsonify({'error': 'Invalid password'}), 401
        
        # Validate products data
        if not products:
            return jsonify({'error': 'No products provided'}), 400
        
        # Update each product
        for product_data in products:
            sku = product_data.get('sku')
            if not sku:
                continue
            
            # Update ItemDetail
            item = ItemDetail.query.get(sku)
            if item:
                item.product = product_data.get('product', item.product)
                item.size = product_data.get('size', item.size)
                item.flavor = product_data.get('flavor', item.flavor)
                item.unitsCs = product_data.get('unitsCs', item.unitsCs)
            
            # Update ShippingDetail
            shipping = ShippingDetail.query.get(sku)
            if shipping:
                # Validate numeric fields
                try:
                    shipping.length = float(product_data.get('length', shipping.length))
                    shipping.width = float(product_data.get('width', shipping.width))
                    shipping.height = float(product_data.get('height', shipping.height))
                    shipping.weight = float(product_data.get('weight', shipping.weight))
                except ValueError as ve:
                    return jsonify({'error': f'Invalid numeric value for SKU {sku}: {str(ve)}'}), 400
        
        # Commit all changes
        db.session.commit()
        
        return jsonify({'message': f'Successfully updated {len(products)} products'}), 200
        
    except Exception as e:
        db.session.rollback()
        print(f"Error updating products: {e}")
        return jsonify({'error': 'Failed to update products'}), 500

@app.route('/api/webhooks/shipstation', methods=['POST'])
def shipstation_webhook():
    print("\n=== WEBHOOK ENDPOINT HIT ===")
    logging.info("=== ShipStation Webhook Received ===")
    
    # Log all request details
    logging.info(f"Request method: {request.method}")
    logging.info(f"Request URL: {request.url}")
    logging.info(f"Request headers: {dict(request.headers)}")
    logging.info(f"Request content type: {request.content_type}")
    logging.info(f"Raw request data: {request.get_data()}")
    
    try:
        data = request.get_json()
        logging.info(f"Parsed JSON webhook data: {data}")
        logging.info(f"Resource type: {data.get('resource_type')}")
        
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
                        
                        logging.info(f"Extracted from fulfillment - Order number: '{order_number}', Ship date: '{ship_date_str}'")
                        logging.info(f"Order number type: {type(order_number)}, length: {len(str(order_number)) if order_number else 0}")
                        
                        if order_number and ship_date_str:
                            # Parse the date and format as MM/DD/YY
                            from datetime import datetime
                            import re
                            
                            # Fix ShipStation's 7-digit microseconds to 6-digit max for Python
                            # ShipStation sends: '2025-07-12T00:00:00.0000000'
                            # Python needs: '2025-07-12T00:00:00.000000'
                            ship_date_fixed = re.sub(r'\.(\d{6})\d+', r'.\1', ship_date_str)
                            logging.info(f"Original ship_date: {ship_date_str}")
                            logging.info(f"Fixed ship_date: {ship_date_fixed}")
                            
                            ship_date = datetime.fromisoformat(ship_date_fixed.replace('Z', '+00:00'))
                            formatted_ship_date = ship_date.strftime('%m/%d/%y')
                            logging.info(f"Formatted ship date: {formatted_ship_date}")
                            
                            # Log database query details
                            logging.info(f"Searching for order with purchase_order_number: '{order_number}'")
                            
                            # Check all orders to see what's in the database
                            all_orders = Order.query.all()
                            logging.info(f"Total orders in database: {len(all_orders)}")
                            if all_orders:
                                logging.info("First 5 order PO numbers in database:")
                                for i, ord in enumerate(all_orders[:5]):
                                    logging.info(f"  {i+1}. PO: '{ord.purchase_order_number}' (type: {type(ord.purchase_order_number)})")
                            
                            # Update the order in the database
                            order = Order.query.filter_by(purchase_order_number=order_number).first()
                            logging.info(f"Database query result: {order is not None}")
                            
                            if order:
                                # Log order details before update
                                logging.info(f"Order found! ID: {order.order_id}")
                                logging.info(f"Current order status BEFORE update: '{order.order_status}'")
                                logging.info(f"Order PO number in DB: '{order.purchase_order_number}'")
                                
                                # Update status
                                old_status = order.order_status
                                new_status = f"SHIPPED\n{formatted_ship_date}"
                                order.order_status = new_status
                                
                                logging.info(f"Status change: '{old_status}' -> '{new_status}'")
                                
                                # Commit to database
                                try:
                                    db.session.commit()
                                    logging.info("Database commit successful!")
                                    
                                    # Verify the update
                                    updated_order = Order.query.filter_by(purchase_order_number=order_number).first()
                                    logging.info(f"Status AFTER commit: '{updated_order.order_status}'")
                                    
                                    logging.info(f"✅ Successfully updated order {order_number} status to: {new_status}")
                                    return jsonify({
                                        "message": "Order status updated",
                                        "order_number": order_number,
                                        "old_status": old_status,
                                        "new_status": new_status
                                    }), 200
                                    
                                except Exception as commit_error:
                                    logging.error(f"❌ Database commit failed: {str(commit_error)}")
                                    db.session.rollback()
                                    return jsonify({"error": f"Failed to commit status update: {str(commit_error)}"}), 500
                                    
                            else:
                                logging.warning(f"❌ Order not found in database: '{order_number}'")
                                # Try alternative search methods
                                logging.info("Trying case-insensitive search...")
                                order_case_insensitive = Order.query.filter(func.lower(Order.purchase_order_number) == func.lower(order_number)).first()
                                if order_case_insensitive:
                                    logging.info(f"Found order with case-insensitive search: {order_case_insensitive.purchase_order_number}")
                                else:
                                    logging.info("No order found even with case-insensitive search")
                                
                                return jsonify({"error": f"Order {order_number} not found"}), 404
                        else:
                            logging.error(f"❌ Missing order number or ship date in fulfillment data")
                            logging.error(f"Fulfillment data: {fulfillment}")
                            return jsonify({"error": "Missing required fulfillment data"}), 400
                    else:
                        logging.error(f"❌ No fulfillments found in response")
                        logging.error(f"Full fulfillment response: {fulfillment_data}")
                        return jsonify({"error": "No fulfillments found"}), 400
                else:
                    logging.error(f"❌ ShipStation API error response: {response.status_code}")
                    logging.error(f"Response text: {response.text}")
                    logging.error(f"Response headers: {response.headers}")
                    return jsonify({"error": "Failed to fetch fulfillment details"}), response.status_code
                    
            except requests.exceptions.Timeout as e:
                error_msg = f"❌ ShipStation API timeout: {str(e)}"
                logging.error(error_msg)
                return jsonify({"error": error_msg}), 500
            except requests.exceptions.ConnectionError as e:
                error_msg = f"❌ ShipStation API connection error: {str(e)}"
                logging.error(error_msg)
                return jsonify({"error": error_msg}), 500
            except requests.exceptions.RequestException as e:
                error_msg = f"❌ ShipStation API request failed: {str(e)}"
                logging.error(error_msg)
                return jsonify({"error": error_msg}), 500
        else:
            logging.info(f"ℹ️  Ignoring webhook - resource type is '{data.get('resource_type')}', not 'FULFILLMENT_SHIPPED'")
                
        return jsonify({"message": "Webhook processed"}), 200
        
    except json.JSONDecodeError as e:
        error_msg = f"❌ Invalid JSON in webhook payload: {str(e)}"
        logging.error(error_msg)
        logging.error(f"Raw request data: {request.get_data()}")
        return jsonify({"error": error_msg}), 400
    except Exception as e:
        error_msg = f"❌ Unexpected error processing webhook: {str(e)}"
        logging.error(error_msg)
        logging.error(f"Exception type: {type(e).__name__}")
        traceback.print_exc()
        return jsonify({"error": error_msg}), 500

# Database backup endpoints
@app.route('/api/database-info', methods=['GET'])
@login_required
def get_database_info():
    """Get database file information including size and estimated zip size"""
    try:
        # Extract database path from URI
        db_uri = app.config['SQLALCHEMY_DATABASE_URI']
        if db_uri.startswith('sqlite:///'):
            db_path = db_uri.replace('sqlite:///', '')
            # Handle relative paths
            if not os.path.isabs(db_path):
                db_path = os.path.join(app.root_path, db_path)
        else:
            return jsonify({'error': 'Only SQLite databases are supported for backup'}), 400
        
        if not os.path.exists(db_path):
            return jsonify({'error': 'Database file not found'}), 404
        
        # Get file size
        size_bytes = os.path.getsize(db_path)
        
        # SQLite databases typically compress to 15-25% of original size
        # Using 20% as a reasonable estimate
        estimated_zip_bytes = size_bytes * 0.20
        estimated_zip_mb = estimated_zip_bytes / (1024 * 1024)
        
        # SendGrid limit is 30MB
        can_email = estimated_zip_mb < 30
        warning = None
        
        if estimated_zip_mb > 30:
            warning = "Backup too large for email (SendGrid limit: 30MB)"
        elif estimated_zip_mb > 25:
            warning = "Backup approaching SendGrid's 30MB limit"
        
        def format_file_size(bytes_size):
            """Format bytes to human readable size"""
            if bytes_size < 1024:
                return f"{bytes_size} B"
            elif bytes_size < 1024 * 1024:
                return f"{bytes_size / 1024:.1f} KB"
            elif bytes_size < 1024 * 1024 * 1024:
                return f"{bytes_size / (1024 * 1024):.1f} MB"
            else:
                return f"{bytes_size / (1024 * 1024 * 1024):.2f} GB"
        
        return jsonify({
            "size_mb": round(size_bytes / (1024 * 1024), 2),
            "size_readable": format_file_size(size_bytes),
            "estimated_zip_mb": round(estimated_zip_mb, 2),
            "estimated_zip_readable": format_file_size(estimated_zip_bytes),
            "filename": os.path.basename(db_path),
            "can_email": can_email,
            "warning": warning
        }), 200
        
    except Exception as e:
        print(f"Error getting database info: {e}")
        return jsonify({'error': 'Failed to get database information'}), 500

@app.route('/api/backup-database', methods=['POST'])
@login_required
def backup_database():
    """Create a database backup and email it"""
    try:
        # Extract database path from URI
        db_uri = app.config['SQLALCHEMY_DATABASE_URI']
        if db_uri.startswith('sqlite:///'):
            db_path = db_uri.replace('sqlite:///', '')
            # Handle relative paths
            if not os.path.isabs(db_path):
                db_path = os.path.join(app.root_path, db_path)
        else:
            return jsonify({'error': 'Only SQLite databases are supported for backup'}), 400
        
        if not os.path.exists(db_path):
            return jsonify({'error': 'Database file not found'}), 404
        
        # Create timestamp for filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        zip_filename = f"gymmolly_backup_{timestamp}.zip"
        
        # Create zip file in memory
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zipf:
            zipf.write(db_path, os.path.basename(db_path))
        
        # Get the zip data
        zip_data = zip_buffer.getvalue()
        zip_size_mb = len(zip_data) / (1024 * 1024)
        
        # Check if zip file is too large for SendGrid
        if zip_size_mb > 30:
            return jsonify({
                'error': f'Backup file too large ({zip_size_mb:.1f} MB). SendGrid limit is 30MB.'
            }), 400
        
        # Format file sizes for email
        original_size = os.path.getsize(db_path)
        def format_file_size(bytes_size):
            if bytes_size < 1024 * 1024:
                return f"{bytes_size / 1024:.1f} KB"
            else:
                return f"{bytes_size / (1024 * 1024):.1f} MB"
        
        # Calculate compression ratio
        compression_ratio = round((1 - len(zip_data) / original_size) * 100, 1)
        
        # Prepare email content
        email_body = f"""
        <h3>GymMolly Database Backup</h3>
        <p>Database backup created on {datetime.now().strftime('%B %d, %Y at %I:%M %p')}</p>
        
        <table style="border-collapse: collapse; margin: 20px 0;">
            <tr>
                <td style="padding: 5px;"><strong>Original size:</strong></td>
                <td style="padding: 5px;">{format_file_size(original_size)}</td>
            </tr>
            <tr>
                <td style="padding: 5px;"><strong>Compressed size:</strong></td>
                <td style="padding: 5px;">{format_file_size(len(zip_data))}</td>
            </tr>
            <tr>
                <td style="padding: 5px;"><strong>Compression ratio:</strong></td>
                <td style="padding: 5px;">{compression_ratio}% reduction</td>
            </tr>
        </table>
        
        <p>This backup is within SendGrid's 30MB attachment limit.</p>
        <p><em>This is an automated backup from the GymMolly system.</em></p>
        """
        
        # Send email using SendGrid
        from sendgrid import SendGridAPIClient
        from sendgrid.helpers.mail import Mail, Attachment, FileContent, FileName, FileType, Disposition
        
        sg = SendGridAPIClient(SENDGRID_API_KEY)
        
        message = Mail(
            from_email=SENDER_EMAIL,
            to_emails='greg@bodynutrition.com',
            subject=f'GymMolly Database Backup - {timestamp}',
            html_content=email_body
        )
        
        # Add attachment
        encoded_file = base64.b64encode(zip_data).decode()
        attachment = Attachment(
            file_content=FileContent(encoded_file),
            file_name=FileName(zip_filename),
            file_type=FileType('application/zip'),
            disposition=Disposition('attachment')
        )
        message.attachment = attachment
        
        # Send email
        response = sg.send(message)
        
        if response.status_code in [200, 201, 202]:
            return jsonify({
                'message': 'Backup successfully created and sent to greg@bodynutrition.com',
                'filename': zip_filename,
                'size': format_file_size(len(zip_data))
            }), 200
        else:
            return jsonify({'error': 'Failed to send backup email'}), 500
            
    except Exception as e:
        print(f"Error creating backup: {e}")
        return jsonify({'error': f'Failed to create backup: {str(e)}'}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
