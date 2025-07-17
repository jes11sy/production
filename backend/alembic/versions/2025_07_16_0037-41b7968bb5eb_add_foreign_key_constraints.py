"""Add foreign key constraints

Revision ID: 41b7968bb5eb
Revises: 001
Create Date: 2025-07-16 00:37:16.084287

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '41b7968bb5eb'
down_revision = '001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add foreign key constraints
    
    # AdvertisingCampaign -> City
    op.create_foreign_key(
        'fk_advertising_campaigns_city_id',
        'advertising_campaigns', 'cities',
        ['city_id'], ['id'],
        ondelete='RESTRICT'
    )
    
    # Master -> City
    op.create_foreign_key(
        'fk_masters_city_id',
        'masters', 'cities',
        ['city_id'], ['id'],
        ondelete='RESTRICT'
    )
    
    # Employee -> Role
    op.create_foreign_key(
        'fk_employees_role_id',
        'employees', 'roles',
        ['role_id'], ['id'],
        ondelete='RESTRICT'
    )
    
    # Employee -> City
    op.create_foreign_key(
        'fk_employees_city_id',
        'employees', 'cities',
        ['city_id'], ['id'],
        ondelete='SET NULL'
    )
    
    # Administrator -> Role
    op.create_foreign_key(
        'fk_administrators_role_id',
        'administrators', 'roles',
        ['role_id'], ['id'],
        ondelete='RESTRICT'
    )
    
    # Request -> AdvertisingCampaign
    op.create_foreign_key(
        'fk_requests_advertising_campaign_id',
        'requests', 'advertising_campaigns',
        ['advertising_campaign_id'], ['id'],
        ondelete='SET NULL'
    )
    
    # Request -> City
    op.create_foreign_key(
        'fk_requests_city_id',
        'requests', 'cities',
        ['city_id'], ['id'],
        ondelete='RESTRICT'
    )
    
    # Request -> RequestType
    op.create_foreign_key(
        'fk_requests_request_type_id',
        'requests', 'request_types',
        ['request_type_id'], ['id'],
        ondelete='RESTRICT'
    )
    
    # Request -> Direction
    op.create_foreign_key(
        'fk_requests_direction_id',
        'requests', 'directions',
        ['direction_id'], ['id'],
        ondelete='SET NULL'
    )
    
    # Request -> Master
    op.create_foreign_key(
        'fk_requests_master_id',
        'requests', 'masters',
        ['master_id'], ['id'],
        ondelete='SET NULL'
    )
    
    # Transaction -> City
    op.create_foreign_key(
        'fk_transactions_city_id',
        'transactions', 'cities',
        ['city_id'], ['id'],
        ondelete='RESTRICT'
    )
    
    # Transaction -> TransactionType
    op.create_foreign_key(
        'fk_transactions_transaction_type_id',
        'transactions', 'transaction_types',
        ['transaction_type_id'], ['id'],
        ondelete='RESTRICT'
    )
    
    # File -> Request
    op.create_foreign_key(
        'fk_files_request_id',
        'files', 'requests',
        ['request_id'], ['id'],
        ondelete='CASCADE'
    )
    
    # File -> Transaction
    op.create_foreign_key(
        'fk_files_transaction_id',
        'files', 'transactions',
        ['transaction_id'], ['id'],
        ondelete='CASCADE'
    )


def downgrade() -> None:
    # Drop foreign key constraints in reverse order
    op.drop_constraint('fk_files_transaction_id', 'files', type_='foreignkey')
    op.drop_constraint('fk_files_request_id', 'files', type_='foreignkey')
    op.drop_constraint('fk_transactions_transaction_type_id', 'transactions', type_='foreignkey')
    op.drop_constraint('fk_transactions_city_id', 'transactions', type_='foreignkey')
    op.drop_constraint('fk_requests_master_id', 'requests', type_='foreignkey')
    op.drop_constraint('fk_requests_direction_id', 'requests', type_='foreignkey')
    op.drop_constraint('fk_requests_request_type_id', 'requests', type_='foreignkey')
    op.drop_constraint('fk_requests_city_id', 'requests', type_='foreignkey')
    op.drop_constraint('fk_requests_advertising_campaign_id', 'requests', type_='foreignkey')
    op.drop_constraint('fk_administrators_role_id', 'administrators', type_='foreignkey')
    op.drop_constraint('fk_employees_city_id', 'employees', type_='foreignkey')
    op.drop_constraint('fk_employees_role_id', 'employees', type_='foreignkey')
    op.drop_constraint('fk_masters_city_id', 'masters', type_='foreignkey')
    op.drop_constraint('fk_advertising_campaigns_city_id', 'advertising_campaigns', type_='foreignkey') 