#!/usr/bin/env python3
"""
Add database indexes for performance optimization
"""

from config import app, db
from sqlalchemy import text

def add_indexes():
    """Add indexes to improve query performance"""
    
    with app.app_context():
        with db.engine.connect() as conn:
            # Create indexes for foreign keys and frequently queried columns
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
                    print(f"✓ Created index: {index_sql.split('idx_')[1].split(' ')[0]}")
                except Exception as e:
                    print(f"✗ Failed to create index: {e}")
            
            conn.commit()
            print("\nDatabase indexes created successfully!")

if __name__ == "__main__":
    print("Adding database indexes...")
    add_indexes()