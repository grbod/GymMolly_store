from alembic import op
import sqlalchemy as sa

def upgrade():
    # Add order_status column with check constraint
    with op.batch_alter_table('orders') as batch_op:
        batch_op.add_column(
            sa.Column(
                'order_status',
                sa.String(20),
                nullable=False,
                server_default='Processing'  # This sets default for existing rows
            )
        )
    
    # Add check constraint for valid status values
    op.create_check_constraint(
        'valid_order_status',
        'orders',
        "order_status IN ('Processing', 'Shipped', 'Voided')"
    )

def downgrade():
    # Remove the check constraint first
    op.drop_constraint('valid_order_status', 'orders')
    
    # Then remove the column
    with op.batch_alter_table('orders') as batch_op:
        batch_op.drop_column('order_status')