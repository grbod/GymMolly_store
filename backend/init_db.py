from main import app, db, ItemDetail, InventoryQuantity, ShippingDetail, ShippingAddress, Order, OrderItem
from sqlalchemy import text
from datetime import datetime, timedelta, UTC

def clear_database():
    try:
        # Update TRUNCATE statement
        db.session.execute(text('TRUNCATE TABLE shipping_addresses, shipping_detail, inventory_quantity, item_detail RESTART IDENTITY CASCADE'))
        db.session.commit()
        print("Cleared existing data from database")
    except Exception as e:
        print(f"Error clearing database: {e}")
        db.session.rollback()

def add_sample_data():
    # Sample item details
    item_details = [
        {'sku': 'GMPROCHOC2-cs', 'product': 'Whey Protein', 'size': '2lb', 'flavor': 'Chocolate', 'unitsCs': '6/cs'},
        {'sku': 'GMPROCINN2-cs', 'product': 'Whey Protein', 'size': '2lb', 'flavor': 'Cinnamon Roll', 'unitsCs': '6/cs'},
        {'sku': 'GMPROCNC2-cs', 'product': 'Whey Protein', 'size': '2lb', 'flavor': 'Cookies & Cream', 'unitsCs': '6/cs'},
        {'sku': 'GYMBCAABR30-cs', 'product': 'After Party', 'size': '30serv', 'flavor': 'BlueRazz', 'unitsCs': '6/cs'},
        {'sku': 'GYMBCAAKW30-cs', 'product': 'After Party', 'size': '30serv', 'flavor': 'Straw-Kiwi', 'unitsCs': '6/cs'},
        {'sku': 'GYMOLBLURAZ30-cs', 'product': 'PRO Preworkout', 'size': '30serv', 'flavor': 'BlueRazz', 'unitsCs': '12/cs'},
        {'sku': 'GYMOLKSBRW30-cs', 'product': 'PRO Preworkout', 'size': '30serv', 'flavor': 'Straw-Kiwi', 'unitsCs': '12/cs'},
        {'sku': 'GYMOLCREA57-cs', 'product': 'Creatine Hcl', 'size': '30serv', 'flavor': 'Unflavored', 'unitsCs': '20/cs'},
    ]

    # Sample inventory quantities
    inventory_quantities = [
        {'sku': 'GMPROCHOC2-cs', 'quantity': 100},
        {'sku': 'GMPROCINN2-cs', 'quantity': 120},
        {'sku': 'GMPROCNC2-cs', 'quantity': 130},
        {'sku': 'GYMBCAABR30-cs', 'quantity': 145},
        {'sku': 'GYMBCAAKW30-cs', 'quantity': 150},
        {'sku': 'GYMOLBLURAZ30-cs', 'quantity': 160},
        {'sku': 'GYMOLKSBRW30-cs', 'quantity': 170},
        {'sku': 'GYMOLCREA57-cs', 'quantity': 200},
    ]

    # Sample shipping details
    shipping_details = [
        {'sku': 'GMPROCHOC2-cs', 'length': 17.375, 'width': 11.75, 'height': 10.25, 'weight': 15.2},
        {'sku': 'GMPROCINN2-cs', 'length': 17.375, 'width': 11.75, 'height': 10.25, 'weight': 15.2},
        {'sku': 'GMPROCNC2-cs', 'length': 17.375, 'width': 11.75, 'height': 10.25, 'weight': 15.2},
        {'sku': 'GYMBCAABR30-cs', 'length': 11.25, 'width': 7.75, 'height': 6.25, 'weight': 6.2},
        {'sku': 'GYMBCAAKW30-cs', 'length': 11.25, 'width': 7.75, 'height': 6.25, 'weight': 6.2},
        {'sku': 'GYMOLBLURAZ30-cs', 'length': 20.25, 'width': 15.25, 'height': 7, 'weight': 19.3},
        {'sku': 'GYMOLKSBRW30-cs', 'length': 20.25, 'width': 15.25, 'height': 7, 'weight': 18.7},
        {'sku': 'GYMOLCREA57-cs', 'length': 12.25, 'width': 9.5, 'height': 7.5, 'weight': 5.6},
    ]

    # Updated sample shipping addresses
    shipping_addresses = [
        {
            'nickname': 'Gym Molly HQ',
            'companyName': 'Greg Booth',
            'addressLine1': '801 S Miami Ave',
            'addressLine2': 'Unit 2104',
            'city': 'Miami',
            'state': 'FL',
            'zipCode': '33130',
            'phone': '',
            'email': ''
        },
        {
            'nickname': 'GNC 2086 Ruston La',
            'companyName': 'GNC Ruston - 2086',
            'addressLine1': '1405 Eagle Drive',
            'addressLine2': 'Box #11',
            'city': 'Ruston',
            'state': 'LA',
            'zipCode': '71270',
            'phone': '(318) 513-1156',
            'email': ''
        },
        {
            'nickname': 'GNC 3059 Marietta GA',
            'companyName': 'GNC 3059',
            'addressLine1': 'West Cobb Marketplace',
            'addressLine2': '2500 Dallas Hwy, Ste 501',
            'city': 'Marietta',
            'state': 'GA',
            'zipCode': '30064',
            'phone': '(678) 581-0334',
            'email': ''
        },
        {
            'nickname': 'GNC 951 Smyrna GA',
            'companyName': 'GNC 951',
            'addressLine1': 'Highland Station',
            'addressLine2': '4480 South Cobb Dr, Ste G',
            'city': 'Smyrna',
            'state': 'GA',
            'zipCode': '30080',
            'phone': '(770) 436-0705',
            'email': ''
        },
        {
            'nickname': 'GNC 1672 Gainesville GA',
            'companyName': 'GNC 1672',
            'addressLine1': 'Village Shoppes at Gainesville',
            'addressLine2': '891 Dawsonville Hwy, Ste 180',
            'city': 'Gainesville',
            'state': 'GA',
            'zipCode': '30501',
            'phone': '(770) 718-9638',
            'email': ''
        },
        {
            'nickname': 'GNC 6077 San Antonio TX',
            'companyName': 'GNC Store #6077 (Potranco) Potranco/1604',
            'addressLine1': '430 W Loop 1604 N, suite #105',
            'addressLine2': '',
            'city': 'San Antonio',
            'state': 'TX',
            'zipCode': '78251',
            'phone': '(210) 468-2623',
            'email': ''
        },
        {
            'nickname': 'GNC KK#3445 Cedar Park TX',
            'companyName': 'GNC KK#3445',
            'addressLine1': '1335 E. Whitestone BLVD. E400',
            'addressLine2': '',
            'city': 'Cedar Park',
            'state': 'TX',
            'zipCode': '78613',
            'phone': '512-259-1246',
            'email': ''
        },
        {
            'nickname': 'GNC KK#9381 Austin TX',
            'companyName': 'GNC KK#9381 (North Hills HEB Shopping Center)',
            'addressLine1': '4815 W. Braker Lane Suite 560',
            'addressLine2': '',
            'city': 'Austin',
            'state': 'TX',
            'zipCode': '78759',
            'phone': '(512) 358-6187',
            'email': ''
        },
        {
            'nickname': 'GNC Laredo',
            'companyName': 'GNC Laredo',
            'addressLine1': '7815 McPherson Rd',
            'addressLine2': '#111',
            'city': 'Laredo',
            'state': 'TX',
            'zipCode': '78045',
            'phone': '(956) 722-2633',
            'email': ''
        },
        {
            'nickname': 'GNC 6519 San Antonio TX',
            'companyName': 'GNC 6519 (Huebner Oaks Shopping Center)',
            'addressLine1': '11075 IH-10 WEST #307',
            'addressLine2': '',
            'city': 'SAN ANTONIO',
            'state': 'TX',
            'zipCode': '78230',
            'phone': '(210) 690-2162',
            'email': ''
        },
        {
            'nickname': 'Rev Nutrition Bakersfield CA',
            'companyName': 'Rev Nutrition',
            'addressLine1': '2600 oswell',
            'addressLine2': 'suite C',
            'city': 'Bakersfield',
            'state': 'CA',
            'zipCode': '93306',
            'phone': '',
            'email': ''
        }
    ]

    # Sample orders
    sample_orders = [
        {
            'purchase_order_number': 'PO-2024-001',
            'shipping_address_id': 1,  # Gym Molly HQ
            'created_at': datetime.now(UTC) - timedelta(days=5),
            'shipping_method': 'Ground'
        },
        {
            'purchase_order_number': 'PO-2024-002',
            'shipping_address_id': 2,  # GNC Ruston
            'created_at': datetime.now(UTC) - timedelta(days=3),
            'shipping_method': 'Express'
        },
        {
            'purchase_order_number': 'PO-2024-003',
            'shipping_address_id': 3,  # GNC Marietta
            'created_at': datetime.now(UTC) - timedelta(days=2),
            'shipping_method': 'Ground'
        },
        {
            'purchase_order_number': 'PO-2024-004',
            'shipping_address_id': 4,  # GNC Smyrna
            'created_at': datetime.now(UTC) - timedelta(days=1),
            'shipping_method': 'Ground'
        },
        {
            'purchase_order_number': 'PO-2024-005',
            'shipping_address_id': 5,  # GNC Gainesville
            'created_at': datetime.now(UTC),
            'shipping_method': 'Express'
        }
    ]

    # Add sample order items after the sample_orders list
    sample_order_items = [
        # Items for PO-2024-001
        {
            'order_id': 1,
            'product_sku': 'GMPROCHOC2-cs',
            'quantity': 2
        },
        {
            'order_id': 1,
            'product_sku': 'GMPROCINN2-cs',
            'quantity': 1
        },
        
        # Items for PO-2024-002
        {
            'order_id': 2,
            'product_sku': 'GYMBCAABR30-cs',
            'quantity': 3
        },
        {
            'order_id': 2,
            'product_sku': 'GYMOLCREA57-cs',
            'quantity': 2
        },
        
        # Items for PO-2024-003
        {
            'order_id': 3,
            'product_sku': 'GMPROCNC2-cs',
            'quantity': 1
        },
        {
            'order_id': 3,
            'product_sku': 'GYMOLBLURAZ30-cs',
            'quantity': 2
        },
        
        # Items for PO-2024-004
        {
            'order_id': 4,
            'product_sku': 'GYMBCAAKW30-cs',
            'quantity': 2
        },
        {
            'order_id': 4,
            'product_sku': 'GYMOLKSBRW30-cs',
            'quantity': 1
        },
        
        # Items for PO-2024-005
        {
            'order_id': 5,
            'product_sku': 'GMPROCHOC2-cs',
            'quantity': 3
        },
        {
            'order_id': 5,
            'product_sku': 'GYMOLCREA57-cs',
            'quantity': 4
        }
    ]

    try:
        # Add item details
        for item in item_details:
            new_item = ItemDetail(**item)
            db.session.add(new_item)

        db.session.flush()  # Flush after each related set of records

        # Add inventory quantities
        for quantity in inventory_quantities:
            new_quantity = InventoryQuantity(**quantity)
            db.session.add(new_quantity)

        db.session.flush()

        # Add shipping details
        for detail in shipping_details:
            new_detail = ShippingDetail(**detail)
            db.session.add(new_detail)

        db.session.flush()

        # Add shipping addresses
        for address in shipping_addresses:
            new_address = ShippingAddress(**address)
            db.session.add(new_address)

        db.session.flush()

        # Add orders
        print("Adding sample orders...")
        for order_data in sample_orders:
            new_order = Order(**order_data)
            db.session.add(new_order)

        db.session.commit()
        print("Sample data including orders added successfully")

        # After adding orders, add order items
        print("Adding sample order items...")
        for item_data in sample_order_items:
            new_order_item = OrderItem(**item_data)
            db.session.add(new_order_item)

        db.session.commit()
        print("Sample data including orders and order items added successfully")
    except Exception as e:
        print(f"Error adding sample data: {e}")
        db.session.rollback()
        raise

if __name__ == '__main__':
    with app.app_context():
        try:
            # Drop all existing tables and create new ones
            db.drop_all()
            db.create_all()
            print("Database schema created successfully")
            add_sample_data()
        except Exception as e:
            print(f"Error initializing database: {e}")
