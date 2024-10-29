from main import app, db, ItemDetail, InventoryQuantity, ShippingDetail, ShippingAddress

def clear_database():
    try:
        db.session.query(ItemDetail).delete()
        db.session.query(InventoryQuantity).delete()
        db.session.query(ShippingDetail).delete()
        db.session.query(ShippingAddress).delete()
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

    try:
        # Add item details
        for item in item_details:
            new_item = ItemDetail(**item)
            db.session.add(new_item)

        # Add inventory quantities
        for quantity in inventory_quantities:
            new_quantity = InventoryQuantity(**quantity)
            db.session.add(new_quantity)

        # Add shipping details
        for detail in shipping_details:
            new_detail = ShippingDetail(**detail)
            db.session.add(new_detail)

        # Add shipping addresses
        for address in shipping_addresses:
            new_address = ShippingAddress(**address)
            db.session.add(new_address)

        db.session.commit()
        print("Sample data added successfully")
    except Exception as e:
        print(f"Error adding sample data: {e}")
        db.session.rollback()

if __name__ == '__main__':
    with app.app_context():
        # Drop all existing tables and create new ones
        db.drop_all()
        db.create_all()
        add_sample_data()
