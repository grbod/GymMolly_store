from alembic import op
import sqlalchemy as sa

def upgrade():
    # Create a new table with all columns including the new one
    op.execute("""
        CREATE TABLE orders_new (
            order_id INTEGER PRIMARY KEY,
            purchase_order_number VARCHAR(100) NOT NULL,
            shipping_address_id INTEGER NOT NULL,
            created_at DATETIME,
            attachment BLOB,
            shipping_method VARCHAR(100) NOT NULL,
            order_status VARCHAR(20) NOT NULL DEFAULT 'Processing',
            FOREIGN KEY(shipping_address_id) REFERENCES shipping_addresses(id)
        )
    """)
    
    # Copy data from old table to new table
    op.execute("""
        INSERT INTO orders_new (
            order_id, 
            purchase_order_number, 
            shipping_address_id, 
            created_at, 
            attachment, 
            shipping_method,
            order_status
        )
        SELECT 
            order_id, 
            purchase_order_number, 
            shipping_address_id, 
            created_at, 
            attachment, 
            shipping_method,
            'Processing' as order_status
        FROM orders
    """)
    
    # Drop old table
    op.drop_table('orders')
    
    # Rename new table to original name
    op.rename_table('orders_new', 'orders')
    
    # Add check constraint for valid status values
    op.create_check_constraint(
        'valid_order_status',
        'orders',
        "order_status IN ('Processing', 'Shipped', 'Voided')"
    )

def downgrade():
    # Remove the check constraint first
    op.drop_constraint('valid_order_status', 'orders')
    
    # Create a new table without the order_status column
    op.execute("""
        CREATE TABLE orders_old (
            order_id INTEGER PRIMARY KEY,
            purchase_order_number VARCHAR(100) NOT NULL,
            shipping_address_id INTEGER NOT NULL,
            created_at DATETIME,
            attachment BLOB,
            shipping_method VARCHAR(100) NOT NULL,
            FOREIGN KEY(shipping_address_id) REFERENCES shipping_addresses(id)
        )
    """)
    
    # Copy data back, excluding the order_status column
    op.execute("""
        INSERT INTO orders_old (
            order_id, 
            purchase_order_number, 
            shipping_address_id, 
            created_at, 
            attachment, 
            shipping_method
        )
        SELECT 
            order_id, 
            purchase_order_number, 
            shipping_address_id, 
            created_at, 
            attachment, 
            shipping_method
        FROM orders
    """)
    
    # Drop new table
    op.drop_table('orders')
    
    # Rename old table back to original name
    op.rename_table('orders_old', 'orders')