from datetime import datetime
import io
from flask import request, jsonify, send_file
from flask_cors import CORS
import json
from sendemail import send_order_confirmation_email
from config import app, db
from shipstationcreate import create_shipstation_order

CORS(app, resources={
    r"/api/*": {
        "origins": ["http://localhost:3000"],
        "methods": ["GET", "POST", "PUT", "DELETE"],
        "allow_headers": ["Content-Type"]
    }
})  # Add this right after creating the Flask app

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
    
    # Add this relationship
    items = db.relationship('OrderItem', backref='order', lazy=True)
    
    def to_dict(self):
        return {
            'order_id': self.order_id,
            'purchase_order_number': self.purchase_order_number,
            'shipping_address_id': self.shipping_address_id,
            'created_at': self.created_at,
            'has_attachment': self.attachment is not None,
            'shipping_method': self.shipping_method  # Add this line
        }

class OrderItem(db.Model):
    __tablename__ = 'order_items'
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.order_id'), nullable=False)
    product_sku = db.Column(db.String(100), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    
    def to_dict(self):
        return {
            'id': self.id,
            'order_id': self.order_id,
            'product_sku': self.product_sku,
            'quantity': self.quantity
        }

# Create the database tables
with app.app_context():
    db.create_all()

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
    inventory = db.session.query(ItemDetail, InventoryQuantity).join(InventoryQuantity).all()
    result = []
    for item, quantity in inventory:
        item_dict = item.to_dict()
        item_dict['quantity'] = quantity.quantity
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
        shipping_method = order_data.get('shipping_method')  # Add this line
        items = order_data.get('items', [])

        # Create new order
        new_order = Order(
            purchase_order_number=purchase_order_number,
            shipping_address_id=shipping_address_id,
            shipping_method=shipping_method  # Add this line
        )

        # Handle file attachment if present
        if 'attachment' in request.files:
            file = request.files['attachment']
            if file:
                new_order.attachment = file.read()

        db.session.add(new_order)
        db.session.flush()  # Get the order ID

        # Add order items and prepare items for email
        order_items = []
        email_items = []
        
        # Update inventory quantities
        for item in items:
            # Get current inventory
            inventory = InventoryQuantity.query.get(item['product_sku'])
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
            item_detail = ItemDetail.query.get(item['product_sku'])
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
        shipping_address = ShippingAddress.query.get(shipping_address_id)
        item_details = {item.sku: item for item in ItemDetail.query.all()}

        # Send confirmation email with properly formatted items
        send_order_confirmation_email(
            new_order,
            shipping_address,
            email_items
        )

        # Create ShipStation order
        create_shipstation_order(
            new_order,
            shipping_address,
            order_items,
            item_details,
            db  # Pass the db object here
        )

        return jsonify({"message": "Order created successfully"}), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 400

# Add this route for downloading attachments
@app.route('/api/orders/<int:order_id>/attachment', methods=['GET'])
def get_order_attachment(order_id):
    try:
        order = Order.query.get_or_404(order_id)
        if not order.attachment:
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
        orders = Order.query.all()
        orders_data = []
        for order in orders:
            shipping_address = db.session.get(ShippingAddress, order.shipping_address_id)
            
            items = []
            for item in order.items:
                product = db.session.get(ItemDetail, item.product_sku)
                items.append({
                    'sku': item.product_sku,
                    'product': product.product,
                    'size': product.size,
                    'flavor': product.flavor,
                    'quantity': item.quantity
                })
            
            order_data = {
                'order_id': order.order_id,
                'created_at': order.created_at,
                'purchase_order_number': order.purchase_order_number,
                'shipping_address': shipping_address.to_dict(),
                'items': items,
                'has_attachment': order.attachment is not None,
                'shipping_method': order.shipping_method  # Add this line
            }
            orders_data.append(order_data)
        
        return jsonify(orders_data), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Add this import at the end of the file, just before the if __name__ == '__main__': block
from shipstationcreate import create_shipstation_order

if __name__ == '__main__':
    app.run(debug=True)
