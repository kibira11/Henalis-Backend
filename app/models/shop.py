# app/models/shop.py

"""
SQLAlchemy models for the Shop module.
Includes tables for:
- Categories
- Materials
- Tags
- Items
- Item Images (with upload support)
- Wishlists
"""

from sqlalchemy import (
    Column, String, Text, Integer, Boolean, Numeric, DateTime, ForeignKey,
    Table, UniqueConstraint, Index
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base
import uuid


# -----------------------------------------------------------------------------
# Association table for Item <-> Tag (many-to-many relationship)
# -----------------------------------------------------------------------------
item_tags = Table(
    "item_tags",
    Base.metadata,
    Column("item_id", UUID(as_uuid=True), ForeignKey("items.id", ondelete="CASCADE"), primary_key=True),
    Column("tag_id", UUID(as_uuid=True), ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True),
    UniqueConstraint("item_id", "tag_id", name="uq_item_tag")  # prevent duplicate tags per item
)


# -----------------------------------------------------------------------------
# Category Model
# -----------------------------------------------------------------------------
class Category(Base):
    """
    Represents furniture categories (e.g., Living Room, Bedroom).
    """
    __tablename__ = "categories"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    slug = Column(String(255), unique=True, nullable=False, index=True)  # used for SEO-friendly URLs
    description = Column(Text)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    items = relationship("Item", back_populates="category", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Category(id={self.id}, name='{self.name}')>"


# -----------------------------------------------------------------------------
# Material Model
# -----------------------------------------------------------------------------
class Material(Base):
    """
    Represents materials used in furniture (e.g., Oak, Steel).
    """
    __tablename__ = "materials"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    description = Column(Text)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    items = relationship("Item", back_populates="material", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Material(id={self.id}, name='{self.name}')>"


# -----------------------------------------------------------------------------
# Tag Model
# -----------------------------------------------------------------------------
class Tag(Base):
    """
    Represents tags for filtering items (e.g., "modern", "minimalist").
    """
    __tablename__ = "tags"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), unique=True, nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    items = relationship("Item", secondary=item_tags, back_populates="tags")

    def __repr__(self):
        return f"<Tag(id={self.id}, name='{self.name}')>"


# -----------------------------------------------------------------------------
# Item Model
# -----------------------------------------------------------------------------
class Item(Base):
    """
    Represents furniture items/products (e.g., Sofa, Chair).
    """
    __tablename__ = "items"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    sku = Column(String(100), unique=True, nullable=False, index=True)  # Stock Keeping Unit
    description = Column(Text)
    price_decimal = Column(Numeric(10, 2), nullable=False)
    currency = Column(String(3), default="USD", nullable=False)
    category_id = Column(UUID(as_uuid=True), ForeignKey("categories.id", ondelete="SET NULL"))
    material_id = Column(UUID(as_uuid=True), ForeignKey("materials.id", ondelete="SET NULL"))
    stock_quantity = Column(Integer, default=0, nullable=False)
    likes = Column(Integer, default=0, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    category = relationship("Category", back_populates="items")
    material = relationship("Material", back_populates="items")
    images = relationship("ItemImage", back_populates="item", cascade="all, delete-orphan")  # multiple images per item
    tags = relationship("Tag", secondary=item_tags, back_populates="items")
    wishlist_entries = relationship("Wishlist", back_populates="item", cascade="all, delete-orphan")

    # Indexes for performance
    __table_args__ = (
        Index("ix_items_category_id", "category_id"),
        Index("ix_items_material_id", "material_id"),
        Index("ix_items_is_active", "is_active"),
        Index("ix_items_price", "price_decimal"),
    )

    def __repr__(self):
        return f"<Item(id={self.id}, name='{self.name}', sku='{self.sku}')>"


# -----------------------------------------------------------------------------
# Item Image Model
# -----------------------------------------------------------------------------
class ItemImage(Base):
    """
    Stores uploaded product images.
    Each item can have multiple images.
    One image can be marked as primary (is_primary=True).
    """
    __tablename__ = "item_images"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    item_id = Column(UUID(as_uuid=True), ForeignKey("items.id", ondelete="CASCADE"), nullable=False)

    storage_path = Column(String(500), nullable=False)  # Path in storage (e.g., S3 or local)
    url = Column(String(1000), nullable=False)  # Public URL for access
    is_primary = Column(Boolean, default=False, nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    item = relationship("Item", back_populates="images")

    __table_args__ = (
        Index("ix_item_images_item_id", "item_id"),
        Index("ix_item_images_is_primary", "item_id", "is_primary"),
    )

    def __repr__(self):
        return f"<ItemImage(id={self.id}, item_id={self.item_id}, is_primary={self.is_primary})>"


# -----------------------------------------------------------------------------
# Wishlist Model
# -----------------------------------------------------------------------------
class Wishlist(Base):
    """
    Represents items a user has saved to wishlist.
    Prevents duplicate entries with a unique constraint.
    """
    __tablename__ = "wishlists"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    item_id = Column(UUID(as_uuid=True), ForeignKey("items.id", ondelete="CASCADE"), nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    item = relationship("Item", back_populates="wishlist_entries")

    __table_args__ = (
        UniqueConstraint("user_id", "item_id", name="uq_user_item_wishlist"),
        Index("ix_wishlists_user_id", "user_id"),
    )

    def __repr__(self):
        return f"<Wishlist(id={self.id}, user_id={self.user_id}, item_id={self.item_id})>"
