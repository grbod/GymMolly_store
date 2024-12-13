"""add order status

Revision ID: 1a2b3c4d5e6f
Revises: 
Create Date: 2024-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '1a2b3c4d5e6f'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    # Create temporary table
    op.execute("""
        CREATE TABLE orders_temp (
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

    # Copy data
    op.execute("""
        INSERT INTO orders_temp 
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

    # Drop original table
    op.execute("DROP TABLE orders")

    # Rename temp table to original
    op.execute("ALTER TABLE orders_temp RENAME TO orders")

    # Add check constraint
    op.execute("""
        CREATE TRIGGER enforce_valid_status
        BEFORE INSERT ON orders
        BEGIN
            SELECT CASE
                WHEN NEW.order_status NOT IN ('Processing', 'Shipped', 'Voided')
                THEN RAISE(ABORT, 'Invalid order status')
            END;
        END;
    """)

def downgrade():
    # Create temporary table without order_status
    op.execute("""
        CREATE TABLE orders_temp (
            order_id INTEGER PRIMARY KEY,
            purchase_order_number VARCHAR(100) NOT NULL,
            shipping_address_id INTEGER NOT NULL,
            created_at DATETIME,
            attachment BLOB,
            shipping_method VARCHAR(100) NOT NULL,
            FOREIGN KEY(shipping_address_id) REFERENCES shipping_addresses(id)
        )
    """)

    # Copy data excluding order_status
    op.execute("""
        INSERT INTO orders_temp 
        SELECT 
            order_id,
            purchase_order_number,
            shipping_address_id,
            created_at,
            attachment,
            shipping_method
        FROM orders
    """)

    # Drop trigger and original table
    op.execute("DROP TRIGGER IF EXISTS enforce_valid_status")
    op.execute("DROP TABLE orders")

    # Rename temp table to original
    op.execute("ALTER TABLE orders_temp RENAME TO orders") 