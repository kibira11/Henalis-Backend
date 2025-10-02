# app/schemas/shop.py

"""
Pydantic schemas for request/response validation in the Shop module.
Provides separate Create, Update, and Response models for all entities.
"""

from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import datetime
from uuid import UUID
from decimal import Decimal


# ============================================================================
# Category Schemas
# ============================================================================

class CategoryBase(BaseModel):
    """Base category schema with common fields."""
    name: str = Field(..., min_length=1, max_length=255, examples=["Living Room"])
    slug: str = Field(..., min_length=1, max_length=255, examples=["living-room"])
    description: Optional[str] = Field(None, examples=["Furniture for your living space"])


class CategoryCreate(CategoryBase):
    """Schema for creating a new category."""
    pass


class CategoryUpdate(BaseModel):
    """Schema for updating a category (all fields optional)."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    slug: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None


class CategoryResponse(CategoryBase):
    """Schema for category responses."""
    id: UUID
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# Material Schemas
# ============================================================================

class MaterialBase(BaseModel):
    """Base material schema with common fields."""
    name: str = Field(..., min_length=1, max_length=255, examples=["Oak Wood"])
    description: Optional[str] = Field(None, examples=["High-quality solid oak"])


class MaterialCreate(MaterialBase):
    """Schema for creating a new material."""
    pass


class MaterialUpdate(BaseModel):
    """Schema for updating a material (all fields optional)."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None


class MaterialResponse(MaterialBase):
    """Schema for material responses."""
    id: UUID
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# Tag Schemas
# ============================================================================

class TagBase(BaseModel):
    """Base tag schema."""
    name: str = Field(..., min_length=1, max_length=100, examples=["modern"])


class TagCreate(TagBase):
    """Schema for creating a new tag."""
    pass


class TagUpdate(BaseModel):
    """Schema for updating a tag."""
    name: Optional[str] = Field(None, min_length=1, max_length=100)


class TagResponse(TagBase):
    """Schema for tag responses."""
    id: UUID
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class TagAssignment(BaseModel):
    """Schema for assigning tags to an item."""
    tag_ids: List[UUID] = Field(..., examples=[["uuid1", "uuid2"]])


# ============================================================================
# Item Image Schemas
# ============================================================================

class ItemImageResponse(BaseModel):
    """Schema for item image responses."""
    id: UUID
    item_id: UUID
    storage_path: str
    url: str
    is_primary: bool
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class ItemImageUpdate(BaseModel):
    """Schema for updating item image metadata."""
    is_primary: Optional[bool] = None


# ============================================================================
# Item Schemas
# ============================================================================

class ItemBase(BaseModel):
    """Base item schema with common fields."""
    name: str = Field(..., min_length=1, max_length=255, examples=["Modern Sofa"])
    sku: str = Field(..., min_length=1, max_length=100, examples=["SOFA-001"])
    description: Optional[str] = Field(None, examples=["A comfortable 3-seater sofa"])
    price_decimal: Decimal = Field(..., gt=0, examples=[599.99])
    currency: str = Field(default="USD", min_length=3, max_length=3, examples=["USD"])
    stock_quantity: int = Field(default=0, ge=0, examples=[10])
    is_active: bool = Field(default=True, examples=[True])


class ItemCreate(ItemBase):
    """Schema for creating a new item."""
    category_id: Optional[UUID] = None
    material_id: Optional[UUID] = None
    tag_ids: Optional[List[UUID]] = Field(default=None, examples=[["uuid1", "uuid2"]])


class ItemUpdate(BaseModel):
    """Schema for updating an item (all fields optional)."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    sku: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    price_decimal: Optional[Decimal] = Field(None, gt=0)
    currency: Optional[str] = Field(None, min_length=3, max_length=3)
    category_id: Optional[UUID] = None
    material_id: Optional[UUID] = None
    stock_quantity: Optional[int] = Field(None, ge=0)
    is_active: Optional[bool] = None


class ItemResponse(ItemBase):
    """Schema for item responses (basic info)."""
    id: UUID
    category_id: Optional[UUID]
    material_id: Optional[UUID]
    likes: int
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class ItemDetailResponse(ItemResponse):
    """Schema for detailed item responses including related entities."""
    category: Optional[CategoryResponse] = None
    material: Optional[MaterialResponse] = None
    images: List[ItemImageResponse] = []
    tags: List[TagResponse] = []
    
    model_config = ConfigDict(from_attributes=True)


class ItemListResponse(BaseModel):
    """Schema for paginated item list responses."""
    items: List[ItemResponse]
    meta: dict = Field(..., examples=[{"total": 100, "limit": 12, "offset": 0}])


# ============================================================================
# Wishlist Schemas
# ============================================================================

class WishlistResponse(BaseModel):
    """Schema for wishlist responses."""
    id: UUID
    user_id: UUID
    item_id: UUID
    created_at: datetime
    item: ItemResponse
    
    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# Bulk Operation Schemas
# ============================================================================

class BulkDeleteRequest(BaseModel):
    """Schema for bulk delete operations."""
    ids: List[UUID] = Field(..., min_length=1, examples=[["uuid1", "uuid2"]])


class BulkUpdateRequest(BaseModel):
    """Schema for bulk update operations."""
    ids: List[UUID] = Field(..., min_length=1, examples=[["uuid1", "uuid2"]])
    patch: dict = Field(..., examples=[{"is_active": False}])


# ============================================================================
# Utility Schemas
# ============================================================================

class LikeResponse(BaseModel):
    """Schema for like operation responses."""
    item_id: UUID
    likes: int