# app/routers/shop.py

"""
Shop API routes.
Defines endpoints for categories, materials, tags, items, images, likes, and wishlist.
"""

from fastapi import (
    APIRouter, Depends, HTTPException, status,
    UploadFile, File, Form, Query
)
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional, List
from uuid import UUID
from decimal import Decimal

from app.database import get_db
from app.dependencies import get_current_user, get_current_admin
from app.services.shop_service import ShopService
from app.storage import storage
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
from app.config import settings

router = APIRouter(prefix="/api", tags=["shop"])

# ============================================================================
# Category Endpoints
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
    try:
        await db.commit()
        await db.refresh(db_category)
    except Exception as e:
        await db.rollback()
        raise HTTPException(400, detail=f"Failed to create category: {str(e)}")
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

    try:
        await db.commit()
        await db.refresh(category)
    except Exception as e:
        await db.rollback()
        raise HTTPException(400, detail=f"Failed to update category: {str(e)}")
    return category


@router.patch("/categories", response_model=dict)
async def bulk_update_categories(
    bulk_request: BulkUpdateRequest,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(get_current_admin)
):
    """Bulk update categories by IDs (admin only)."""
    count = await ShopService.bulk_update_entities(db, Category, bulk_request.ids, bulk_request.patch)
    return {"updated": count}


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


@router.delete("/categories", response_model=dict)
async def bulk_delete_categories(
    bulk_request: BulkDeleteRequest,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(get_current_admin)
):
    """Bulk delete categories by IDs (admin only)."""
    count = await ShopService.bulk_delete_entities(db, Category, bulk_request.ids)
    return {"deleted": count}


# ============================================================================
# Material Endpoints
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


@router.get("/materials/{material_id}", response_model=MaterialResponse)
async def get_material(material_id: UUID, db: AsyncSession = Depends(get_db)):
    """Get a material by ID."""
    result = await db.execute(select(Material).where(Material.id == material_id))
    material = result.scalar_one_or_none()
    if not material:
        raise HTTPException(404, detail="Material not found")
    return material


@router.post("/materials", response_model=MaterialResponse, status_code=201)
async def create_material(
    material: MaterialCreate,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(get_current_admin)
):
    """Create a new material (admin only)."""
    db_material = Material(**material.model_dump())
    db.add(db_material)
    try:
        await db.commit()
        await db.refresh(db_material)
    except Exception as e:
        await db.rollback()
        raise HTTPException(400, detail=f"Failed to create material: {str(e)}")
    return db_material


@router.patch("/materials/{material_id}", response_model=MaterialResponse)
async def update_material(
    material_id: UUID,
    material_update: MaterialUpdate,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(get_current_admin)
):
    """Update a material by ID (admin only)."""
    result = await db.execute(select(Material).where(Material.id == material_id))
    material = result.scalar_one_or_none()
    if not material:
        raise HTTPException(404, detail="Material not found")

    update_data = material_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(material, field, value)

    try:
        await db.commit()
        await db.refresh(material)
    except Exception as e:
        await db.rollback()
        raise HTTPException(400, detail=f"Failed to update material: {str(e)}")
    return material


@router.patch("/materials", response_model=dict)
async def bulk_update_materials(
    bulk_request: BulkUpdateRequest,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(get_current_admin)
):
    """Bulk update materials by IDs (admin only)."""
    count = await ShopService.bulk_update_entities(db, Material, bulk_request.ids, bulk_request.patch)
    return {"updated": count}


@router.delete("/materials/{material_id}", status_code=204)
async def delete_material(
    material_id: UUID,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(get_current_admin)
):
    """Delete a material by ID (admin only)."""
    result = await db.execute(select(Material).where(Material.id == material_id))
    material = result.scalar_one_or_none()
    if not material:
        raise HTTPException(404, detail="Material not found")
    await db.delete(material)
    await db.commit()


@router.delete("/materials", response_model=dict)
async def bulk_delete_materials(
    bulk_request: BulkDeleteRequest,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(get_current_admin)
):
    """Bulk delete materials by IDs (admin only)."""
    count = await ShopService.bulk_delete_entities(db, Material, bulk_request.ids)
    return {"deleted": count}


# ============================================================================
# Tag Endpoints
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


@router.get("/tags/{tag_id}", response_model=TagResponse)
async def get_tag(tag_id: UUID, db: AsyncSession = Depends(get_db)):
    """Get a tag by ID."""
    result = await db.execute(select(Tag).where(Tag.id == tag_id))
    tag = result.scalar_one_or_none()
    if not tag:
        raise HTTPException(404, detail="Tag not found")
    return tag


@router.post("/tags", response_model=TagResponse, status_code=201)
async def create_tag(
    tag: TagCreate,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(get_current_admin)
):
    """Create a new tag (admin only)."""
    db_tag = Tag(**tag.model_dump())
    db.add(db_tag)
    try:
        await db.commit()
        await db.refresh(db_tag)
    except Exception as e:
        await db.rollback()
        raise HTTPException(400, detail=f"Failed to create tag: {str(e)}")
    return db_tag


@router.patch("/tags/{tag_id}", response_model=TagResponse)
async def update_tag(
    tag_id: UUID,
    tag_update: TagUpdate,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(get_current_admin)
):
    """Update a tag by ID (admin only)."""
    result = await db.execute(select(Tag).where(Tag.id == tag_id))
    tag = result.scalar_one_or_none()
    if not tag:
        raise HTTPException(404, detail="Tag not found")

    update_data = tag_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(tag, field, value)

    try:
        await db.commit()
        await db.refresh(tag)
    except Exception as e:
        await db.rollback()
        raise HTTPException(400, detail=f"Failed to update tag: {str(e)}")
    return tag


@router.patch("/tags", response_model=dict)
async def bulk_update_tags(
    bulk_request: BulkUpdateRequest,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(get_current_admin)
):
    """Bulk update tags by IDs (admin only)."""
    count = await ShopService.bulk_update_entities(db, Tag, bulk_request.ids, bulk_request.patch)
    return {"updated": count}


@router.delete("/tags/{tag_id}", status_code=204)
async def delete_tag(
    tag_id: UUID,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(get_current_admin)
):
    """Delete a tag by ID (admin only)."""
    result = await db.execute(select(Tag).where(Tag.id == tag_id))
    tag = result.scalar_one_or_none()
    if not tag:
        raise HTTPException(404, detail="Tag not found")
    await db.delete(tag)
    await db.commit()


@router.delete("/tags", response_model=dict)
async def bulk_delete_tags(
    bulk_request: BulkDeleteRequest,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(get_current_admin)
):
    """Bulk delete tags by IDs (admin only)."""
    count = await ShopService.bulk_delete_entities(db, Tag, bulk_request.ids)
    return {"deleted": count}


@router.post("/items/{item_id}/tags", response_model=List[TagResponse])
async def assign_tags_to_item(
    item_id: UUID,
    tag_assignment: TagAssignment,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(get_current_admin)
):
    """Assign tags to an item (admin only)."""
    item_result = await db.execute(select(Item).where(Item.id == item_id))
    item = item_result.scalar_one_or_none()
    if not item:
        raise HTTPException(404, detail="Item not found")

    tags_result = await db.execute(select(Tag).where(Tag.id.in_(tag_assignment.tag_ids)))
    tags = tags_result.scalars().all()
    if len(tags) != len(tag_assignment.tag_ids):
        raise HTTPException(400, detail="Some tags not found")

    for tag in tags:
        if tag not in item.tags:
            item.tags.append(tag)

    await db.commit()
    await db.refresh(item)
    return item.tags


@router.delete("/items/{item_id}/tags/{tag_id}", status_code=204)
async def remove_tag_from_item(
    item_id: UUID,
    tag_id: UUID,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(get_current_admin)
):
    """Remove a tag from an item (admin only)."""
    item_result = await db.execute(select(Item).where(Item.id == item_id))
    item = item_result.scalar_one_or_none()
    if not item:
        raise HTTPException(404, detail="Item not found")

    tag_to_remove = next((t for t in item.tags if t.id == tag_id), None)
    if not tag_to_remove:
        raise HTTPException(404, detail="Tag not found on item")

    item.tags.remove(tag_to_remove)
    await db.commit()
