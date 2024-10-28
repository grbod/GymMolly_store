import requests
import base64
from datetime import datetime
import json
import math
from config import app, db, SS_CLIENT_ID, SS_CLIENT_SECRET, SS_BASE_URL, SS_STORE_ID

# Editable constant for customer note
CUSTOMER_NOTE = "Questions? Please call Greg Booth from Gym Molly at (323) 538-2195"

# Billing Information for Gym Molly FedEx Account
BILLTO_NAME = "Jaiah Kai Kai"
BILLTO_COMPANY = "Gym Molly"
BILLTO_STREET1 = "801 S Miami Ave"
BILLTO_STREET2 = "Unit 2104"
BILLTO_CITY = "Miami"
BILLTO_STATE = "FL"
BILLTO_POSTAL_CODE = "33130"
BILLTO_COUNTRY = "US"
BILLTO_PHONE = "123-456-7890"

# FedEx Shipping Method Mapping
SHIPPING_METHOD_MAPPING = {
    "FedEx Ground": {"code": "fedex_ground", "name": "FedEx Ground®"},
    "FedEx Home Delivery": {"code": "fedex_home_delivery", "name": "FedEx Home Delivery®"},
    "FedEx 2Day": {"code": "fedex_2day", "name": "FedEx 2Day®"},
    "FedEx Express Saver": {"code": "fedex_express_saver", "name": "FedEx Express Saver®"},
    "FedEx Standard Overnight": {"code": "fedex_standard_overnight", "name": "FedEx Standard Overnight®"}
}

def get_auth_header():
    """Generate the Authorization header for ShipStation API"""
    credentials = f"{SS_CLIENT_ID}:{SS_CLIENT_SECRET}"
    encoded_credentials = base64.b64encode(credentials.encode('utf-8')).decode('utf-8')
    return f"Basic {encoded_credentials}"

def create_shipstation_order(order, shipping_address, order_items, item_details, db):
    """Create an order in ShipStation"""
    
    url = f"{SS_BASE_URL}/orders/createorder"
    
    # Get FedEx shipping info
    fedex_shipping_info = SHIPPING_METHOD_MAPPING.get(order.shipping_method, SHIPPING_METHOD_MAPPING["FedEx Ground"])
    
    # Debug: Print shipping method and mapped info
    print(f"Debug: Original shipping method: {order.shipping_method}")
    print(f"Debug: Mapped FedEx shipping info: {fedex_shipping_info}")
    
    # Prepare shipping address
    ship_to = {
        "name": shipping_address.companyName,
        "company": shipping_address.companyName,
        "street1": shipping_address.addressLine1,
        "street2": shipping_address.addressLine2 if shipping_address.addressLine2 else None,
        "city": shipping_address.city,
        "state": shipping_address.state,
        "postalCode": shipping_address.zipCode,
        "country": "US",
        "phone": shipping_address.phone,
        "residential": False
    }
    
    # Prepare order items and fetch shipping details
    items = []
    total_weight = 0
    picking_notes = []
    dimensions = None
    item_count = 1

    session = db.session()
    for order_item in order_items:
        item = item_details.get(order_item.product_sku)
        shipping_detail = session.query(db.Model.metadata.tables['shipping_detail']).filter_by(sku=order_item.product_sku).first()
        
        if item and shipping_detail:
            # Fetch the unitsCs from the item_detail table
            item_detail = session.query(db.Model.metadata.tables['item_detail']).filter_by(sku=order_item.product_sku).first()
            units_cs = item_detail.unitsCs if item_detail else "N/A"

            items.append({
                "sku": order_item.product_sku,
                "name": f"{item.product} - {item.size} - {item.flavor} - {units_cs}",
                "quantity": order_item.quantity,
                "unitPrice": 0,  # Set appropriate price if available
                "adjustment": False
            })
            
            # Round up dimensions
            length = math.ceil(shipping_detail.length)
            width = math.ceil(shipping_detail.width)
            height = math.ceil(shipping_detail.height)
            
            # Convert weight to pounds and ounces
            weight_lbs = int(shipping_detail.weight)
            weight_oz = round((shipping_detail.weight - weight_lbs) * 16)
            
            weight_str = f"{weight_lbs}lbs"
            if weight_oz > 0:
                weight_str += f" {weight_oz}oz"
            
            # Calculate total weight
            item_weight = shipping_detail.weight * order_item.quantity
            total_weight += item_weight
            
            # Enumerate through each item based on quantity
            for _ in range(order_item.quantity):
                picking_notes.append(
                    f"Item {item_count}: {order_item.product_sku} - Box({length}x{width}x{height}) - {weight_str}"
                )
                item_count += 1
            
            if len(order_items) == 1:
                dimensions = {
                    "units": "inches",
                    "length": length,
                    "width": width,
                    "height": height
                }

    session.close()
    
    # Add the shipping method to the picking notes
    picking_notes.append(f"Shipping Method: {order.shipping_method}")
    
    # Prepare order payload
    order_data = {
        "orderNumber": str(order.purchase_order_number),
        "orderDate": order.created_at.isoformat(),
        "orderStatus": "awaiting_shipment",
        "customerUsername": shipping_address.companyName,
        "customerEmail": shipping_address.email,
        "billTo": {
            "name": BILLTO_NAME,
            "company": BILLTO_COMPANY,
            "street1": BILLTO_STREET1,
            "street2": BILLTO_STREET2,
            "city": BILLTO_CITY,
            "state": BILLTO_STATE,
            "postalCode": BILLTO_POSTAL_CODE,
            "country": BILLTO_COUNTRY,
            "phone": BILLTO_PHONE
        },
        "shipTo": ship_to,
        "items": items,
        "carrierCode": "fedex",
        "serviceCode": fedex_shipping_info["code"],
        "packageCode": "package",
        "confirmation": "delivery",
        "requestedShippingService": fedex_shipping_info["code"],
        "weight": {
            "value": total_weight,
            "units": "pounds"
        },
        "advancedOptions": {
            "storeId": SS_STORE_ID,
            "customField1": f"Order ID: {order.order_id}"
        },
        "internalNotes": "\n".join(picking_notes),
        "customerNotes": CUSTOMER_NOTE
    }

    if dimensions:
        order_data["dimensions"] = dimensions
    
    # Debug: Print the entire order payload
    print("Debug: ShipStation Order Payload:")
    print(json.dumps(order_data, indent=2))
    
    # Set headers
    headers = {
        "Authorization": get_auth_header(),
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.post(url, json=order_data, headers=headers)
        response.raise_for_status()
        
        # Debug: Print the response from ShipStation
        print("Debug: ShipStation API Response:")
        print(json.dumps(response.json(), indent=2))
        
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error creating ShipStation order: {str(e)}")
        if hasattr(e.response, 'text'):
            print(f"Response: {e.response.text}")
        raise
