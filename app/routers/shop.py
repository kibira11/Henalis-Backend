# app/routers/shop.py

"""
Shop API routes.
Defines endpoints for categories, materials, tags, items, images, likes, and wishlist.
"""

from fastapi import (
    APIRouter, Depends, HTTPException, status,
    UploadFile, File, Query
)
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional, List
from uuid import UUID
import os, shutil, uuid as uuid_lib

from app.database import get_db
from app.dependencies import get_current_user, get_current_admin
from app.services.shop_service import ShopService
from app.models.shop import Category, Material, Tag, Item, ItemImage, Wishlist
from app.schemas.shop import (
    CategoryCreate, CategoryUpdate, CategoryResponse,
    MaterialCreate, MaterialUpdate, MaterialResponse,
    TagCreate, TagUpdate, TagResponse, TagAssignment,
    ItemCreate, ItemUpdate, ItemResponse, ItemDetailResponse, ItemListResponse,
    ItemImageResponse, ItemImageUpdate,
    WishlistResponse,
    BulkDeleteRequest, BulkUpdateRequest,
    LikeResponse,
)

# Router prefix ensures all endpoints are under /api
router = APIRouter(prefix="/api", tags=["shop"])

# Directory to save uploaded images locally (can later be swapped with S3 or Supabase Storage)
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)


# ============================================================================
# CATEGORY ENDPOINTS
# ============================================================================
@router.get("/categories", response_model=List[CategoryResponse])
async def list_categories(
    q: Optional[str] = Query(None, description="Search by name"),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db)
):
    """List all categories with optional search and pagination."""
    query = select(Category)
    if q:
        query = query.where(Category.name.ilike(f"%{q}%"))
    query = query.order_by(Category.name).limit(limit).offset(offset)
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/categories/{category_id}", response_model=CategoryResponse)
async def get_category(category_id: UUID, db: AsyncSession = Depends(get_db)):
    """Get a category by ID."""
    result = await db.execute(select(Category).where(Category.id == category_id))
    category = result.scalar_one_or_none()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    return category


@router.post("/categories", response_model=CategoryResponse, status_code=201)
async def create_category(
    category: CategoryCreate,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(get_current_admin)
):
    """Create a new category (admin only)."""
    db_category = Category(**category.model_dump())
    db.add(db_category)
    await db.commit()
    await db.refresh(db_category)
    return db_category


@router.patch("/categories/{category_id}", response_model=CategoryResponse)
async def update_category(
    category_id: UUID,
    category_update: CategoryUpdate,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(get_current_admin)
):
    """Update a category by ID (admin only)."""
    result = await db.execute(select(Category).where(Category.id == category_id))
    category = result.scalar_one_or_none()
    if not category:
        raise HTTPException(404, detail="Category not found")

    update_data = category_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(category, field, value)

    await db.commit()
    await db.refresh(category)
    return category


@router.delete("/categories/{category_id}", status_code=204)
async def delete_category(
    category_id: UUID,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(get_current_admin)
):
    """Delete a category by ID (admin only)."""
    result = await db.execute(select(Category).where(Category.id == category_id))
    category = result.scalar_one_or_none()
    if not category:
        raise HTTPException(404, detail="Category not found")
    await db.delete(category)
    await db.commit()


# ============================================================================
# MATERIAL ENDPOINTS
# ============================================================================
@router.get("/materials", response_model=List[MaterialResponse])
async def list_materials(
    q: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db)
):
    """List all materials."""
    query = select(Material)
    if q:
        query = query.where(Material.name.ilike(f"%{q}%"))
    query = query.order_by(Material.name).limit(limit).offset(offset)
    result = await db.execute(query)
    return result.scalars().all()


# ============================================================================
# TAG ENDPOINTS
# ============================================================================
@router.get("/tags", response_model=List[TagResponse])
async def list_tags(
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db)
):
    """List all tags."""
    result = await db.execute(select(Tag).order_by(Tag.name).limit(limit).offset(offset))
    return result.scalars().all()


# ============================================================================
# ITEM IMAGE ENDPOINTS
# ============================================================================
@router.post("/items/{item_id}/images", response_model=ItemImageResponse, status_code=201)
async def upload_item_image(
    item_id: UUID,
    file: UploadFile = File(...),
    is_primary: bool = False,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(get_current_admin)
):
    """
    Upload an image for an item (admin only).
    - Saves file locally under /uploads
    - Stores image metadata in the DB
    """
    result = await db.execute(select(Item).where(Item.id == item_id))
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(404, detail="Item not found")

    ext = file.filename.split(".")[-1]
    unique_name = f"{uuid_lib.uuid4()}.{ext}"
    file_path = os.path.join(UPLOAD_DIR, unique_name)

    # Save to local disk
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    url = f"/{UPLOAD_DIR}/{unique_name}"

    image = ItemImage(
        item_id=item.id,
        storage_path=file_path,
        url=url,
        is_primary=is_primary,
    )
    db.add(image)
    await db.commit()
    await db.refresh(image)
    return image


@router.patch("/items/images/{image_id}", response_model=ItemImageResponse)
async def update_item_image(
    image_id: UUID,
    image_update: ItemImageUpdate,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(get_current_admin)
):
    """Update item image metadata (e.g. set as primary)."""
    result = await db.execute(select(ItemImage).where(ItemImage.id == image_id))
    image = result.scalar_one_or_none()
    if not image:
        raise HTTPException(404, detail="Image not found")

    update_data = image_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(image, field, value)

    await db.commit()
    await db.refresh(image)
    return image


@router.delete("/items/images/{image_id}", status_code=204)
async def delete_item_image(
    image_id: UUID,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(get_current_admin)
):
    """Delete an item image (admin only)."""
    result = await db.execute(select(ItemImage).where(ItemImage.id == image_id))
    image = result.scalar_one_or_none()
    if not image:
        raise HTTPException(404, detail="Image not found")

    # Delete from filesystem
    if os.path.exists(image.storage_path):
        os.remove(image.storage_path)

    await db.delete(image)
    await db.commit()


# ============================================================================
# ITEM DETAIL (with images)
# ============================================================================
@router.get("/items/{item_id}", response_model=ItemDetailResponse)
async def get_item(item_id: UUID, db: AsyncSession = Depends(get_db)):
    """Get detailed item info, including images."""
    result = await db.execute(select(Item).where(Item.id == item_id))
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(404, detail="Item not found")
    return item
