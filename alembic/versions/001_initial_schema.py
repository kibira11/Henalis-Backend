# alembic/versions/001_initial_schema.py

"""Initial schema for Shop module

Revision ID: 001_initial_schema
Revises: 
Create Date: 2024-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

# revision identifiers, used by Alembic.
revision = '001_initial_schema'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create categories table
    op.create_table(
        'categories',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('slug', sa.String(255), unique=True, nullable=False),
        sa.Column('description', sa.Text()),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index('ix_categories_slug', 'categories', ['slug'])
    
    # Create materials table
    op.create_table(
        'materials',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text()),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    
    # Create tags table
    op.create_table(
        'tags',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('name', sa.String(100), unique=True, nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    
    # Create items table
    op.create_table(
        'items',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('sku', sa.String(100), unique=True, nullable=False),
        sa.Column('description', sa.Text()),
        sa.Column('price_decimal', sa.Numeric(10, 2), nullable=False),
        sa.Column('currency', sa.String(3), default='USD', nullable=False),
        sa.Column('category_id', UUID(as_uuid=True), sa.ForeignKey('categories.id', ondelete='SET NULL')),
        sa.Column('material_id', UUID(as_uuid=True), sa.ForeignKey('materials.id', ondelete='SET NULL')),
        sa.Column('stock_quantity', sa.Integer, default=0, nullable=False),
        sa.Column('likes', sa.Integer, default=0, nullable=False),
        sa.Column('is_active', sa.Boolean, default=True, nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index('ix_items_sku', 'items', ['sku'])
    op.create_index('ix_items_category_id', 'items', ['category_id'])
    op.create_index('ix_items_material_id', 'items', ['material_id'])
    op.create_index('ix_items_is_active', 'items', ['is_active'])
    op.create_index('ix_items_price', 'items', ['price_decimal'])
    
    # Create item_images table
    op.create_table(
        'item_images',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('item_id', UUID(as_uuid=True), sa.ForeignKey('items.id', ondelete='CASCADE'), nullable=False),
        sa.Column('storage_path', sa.String(500), nullable=False),
        sa.Column('url', sa.String(1000), nullable=False),
        sa.Column('is_primary', sa.Boolean, default=False, nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index('ix_item_images_item_id', 'item_images', ['item_id'])
    op.create_index('ix_item_images_is_primary', 'item_images', ['item_id', 'is_primary'])
    
    # Create item_tags association table
    op.create_table(
        'item_tags',
        sa.Column('item_id', UUID(as_uuid=True), sa.ForeignKey('items.id', ondelete='CASCADE'), primary_key=True),
        sa.Column('tag_id', UUID(as_uuid=True), sa.ForeignKey('tags.id', ondelete='CASCADE'), primary_key=True),
        sa.UniqueConstraint('item_id', 'tag_id', name='uq_item_tag'),
    )
    
    # Create wishlists table
    op.create_table(
        'wishlists',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', UUID(as_uuid=True), nullable=False),
        sa.Column('item_id', UUID(as_uuid=True), sa.ForeignKey('items.id', ondelete='CASCADE'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint('user_id', 'item_id', name='uq_user_item_wishlist'),
    )
    op.create_index('ix_wishlists_user_id', 'wishlists', ['user_id'])


def downgrade() -> None:
    op.drop_table('wishlists')
    op.drop_table('item_tags')
    op.drop_table('item_images')
    op.drop_table('items')
    op.drop_table('tags')
    op.drop_table('materials')
    op.drop_table('categories')