# app/services/shop_service.py

"""
Business logic layer for the Shop module.
Handles complex operations like filtering, sorting, pagination, and bulk operations.
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, func, or_, and_
from sqlalchemy.orm import selectinload
from typing import Optional, List, Dict, Any
from uuid import UUID
from app.models.shop import (
    Category, Material, Tag, Item, ItemImage, Wishlist, item_tags
)
from app.schemas.shop import ItemUpdate
from fastapi import HTTPException, status
from decimal import Decimal


class ShopService:
    """Service class containing business logic for shop operations."""
    
    @staticmethod
    async def get_items_with_filters(
        db: AsyncSession,
        category: Optional[str] = None,
        material: Optional[str] = None,
        price_min: Optional[Decimal] = None,
        price_max: Optional[Decimal] = None,
        tags: Optional[str] = None,
        is_active: Optional[bool] = None,
        q: Optional[str] = None,
        sort: str = "newest",
        limit: int = 12,
        offset: int = 0,
    ) -> Dict[str, Any]:
        """
        Get items with advanced filtering, sorting, and pagination.
        
        Args:
            db: Database session
            category: Category slug or UUID
            material: Material slug or UUID (not directly filterable by slug in current model)
            price_min: Minimum price filter
            price_max: Maximum price filter
            tags: Comma-separated tag UUIDs
            is_active: Filter by active status
            q: Search query for name and description
            sort: Sort order (newest, price-low, price-high, most-loved)
            limit: Number of items per page
            offset: Pagination offset
            
        Returns:
            Dictionary with 'items' and 'meta' keys
        """
        # Build base query
        query = select(Item)
        
        # Apply filters
        filters = []
        
        # Category filter (by slug or UUID)
        if category:
            try:
                # Try as UUID first
                category_uuid = UUID(category)
                filters.append(Item.category_id == category_uuid)
            except ValueError:
                # Treat as slug - join with category table
                category_subquery = select(Category.id).where(Category.slug == category)
                filters.append(Item.category_id.in_(category_subquery))
        
        # Material filter (by UUID)
        if material:
            try:
                material_uuid = UUID(material)
                filters.append(Item.material_id == material_uuid)
            except ValueError:
                # Could also support material name lookup here
                pass
        
        # Price filters
        if price_min is not None:
            filters.append(Item.price_decimal >= price_min)
        if price_max is not None:
            filters.append(Item.price_decimal <= price_max)
        
        # Active status filter
        if is_active is not None:
            filters.append(Item.is_active == is_active)
        
        # Tags filter (items must have at least one of the specified tags)
        if tags:
            tag_ids = [UUID(tag_id.strip()) for tag_id in tags.split(",") if tag_id.strip()]
            if tag_ids:
                # Subquery to find items with any of the specified tags
                tag_subquery = (
                    select(item_tags.c.item_id)
                    .where(item_tags.c.tag_id.in_(tag_ids))
                    .distinct()
                )
                filters.append(Item.id.in_(tag_subquery))
        
        # Search query (case-insensitive ILIKE on name and description)
        if q:
            search_pattern = f"%{q}%"
            filters.append(
                or_(
                    Item.name.ilike(search_pattern),
                    Item.description.ilike(search_pattern)
                )
            )
        
        # Apply all filters
        if filters:
            query = query.where(and_(*filters))
        
        # Count total matching items
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await db.execute(count_query)
        total = total_result.scalar() or 0
        
        # Apply sorting
        if sort == "newest":
            query = query.order_by(Item.created_at.desc())
        elif sort == "price-low":
            query = query.order_by(Item.price_decimal.asc())
        elif sort == "price-high":
            query = query.order_by(Item.price_decimal.desc())
        elif sort == "most-loved":
            query = query.order_by(Item.likes.desc())
        else:
            # Default to newest
            query = query.order_by(Item.created_at.desc())
        
        # Apply pagination
        query = query.limit(limit).offset(offset)
        
        # Execute query
        result = await db.execute(query)
        items = result.scalars().all()
        
        return {
            "items": items,
            "meta": {
                "total": total,
                "limit": limit,
                "offset": offset,
            }
        }
    
    @staticmethod
    async def get_item_detail(db: AsyncSession, item_id: UUID) -> Optional[Item]:
        """
        Get item with all related data (category, material, images, tags).
        Uses eager loading to avoid N+1 queries.
        
        Args:
            db: Database session
            item_id: Item UUID
            
        Returns:
            Item with all relationships loaded, or None if not found
        """
        query = (
            select(Item)
            .options(
                selectinload(Item.category),
                selectinload(Item.material),
                selectinload(Item.images),
                selectinload(Item.tags),
            )
            .where(Item.id == item_id)
        )
        
        result = await db.execute(query)
        return result.scalar_one_or_none()
    
    @staticmethod
    async def bulk_update_entities(
        db: AsyncSession,
        model_class,
        ids: List[UUID],
        update_data: Dict[str, Any]
    ) -> int:
        """
        Perform bulk update on multiple entities.
        
        Args:
            db: Database session
            model_class: SQLAlchemy model class
            ids: List of entity UUIDs to update
            update_data: Dictionary of fields to update
            
        Returns:
            Number of entities updated
        """
        if not ids or not update_data:
            return 0
        
        # Remove None values from update_data
        update_data = {k: v for k, v in update_data.items() if v is not None}
        
        if not update_data:
            return 0
        
        stmt = (
            update(model_class)
            .where(model_class.id.in_(ids))
            .values(**update_data)
        )
        
        result = await db.execute(stmt)
        await db.commit()
        
        return result.rowcount
    
    @staticmethod
    async def bulk_delete_entities(
        db: AsyncSession,
        model_class,
        ids: List[UUID]
    ) -> int:
        """
        Perform bulk delete on multiple entities.
        
        Args:
            db: Database session
            model_class: SQLAlchemy model class
            ids: List of entity UUIDs to delete
            
        Returns:
            Number of entities deleted
        """
        if not ids:
            return 0
        
        stmt = delete(model_class).where(model_class.id.in_(ids))
        result = await db.execute(stmt)
        await db.commit()
        
        return result.rowcount
    
    @staticmethod
    async def set_primary_image(
        db: AsyncSession,
        image_id: UUID,
        item_id: UUID
    ) -> ItemImage:
        """
        Set an image as primary and unset all other primary images for the item.
        Ensures only one primary image per item.
        
        Args:
            db: Database session
            image_id: Image UUID to set as primary
            item_id: Item UUID
            
        Returns:
            Updated ItemImage
            
        Raises:
            HTTPException: If image not found or doesn't belong to item
        """
        # Verify image exists and belongs to item
        query = select(ItemImage).where(
            ItemImage.id == image_id,
            ItemImage.item_id == item_id
        )
        result = await db.execute(query)
        image = result.scalar_one_or_none()
        
        if not image:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Image not found or doesn't belong to this item"
            )
        
        # Unset all primary flags for this item
        await db.execute(
            update(ItemImage)
            .where(ItemImage.item_id == item_id)
            .values(is_primary=False)
        )
        
        # Set this image as primary
        image.is_primary = True
        await db.commit()
        await db.refresh(image)
        
        return image
    
    @staticmethod
    async def increment_item_likes(db: AsyncSession, item_id: UUID) -> Optional[Item]:
        """
        Increment the likes counter for an item.
        
        Args:
            db: Database session
            item_id: Item UUID
            
        Returns:
            Updated item or None if not found
        """
        # Use atomic update to prevent race conditions
        stmt = (
            update(Item)
            .where(Item.id == item_id)
            .values(likes=Item.likes + 1)
            .returning(Item)
        )
        
        result = await db.execute(stmt)
        await db.commit()
        
        return result.scalar_one_or_none()
    
    @staticmethod
    async def add_to_wishlist(
        db: AsyncSession,
        user_id: UUID,
        item_id: UUID
    ) -> Wishlist:
        """
        Add an item to user's wishlist.
        Idempotent - returns existing entry if already wishlisted.
        
        Args:
            db: Database session
            user_id: User UUID
            item_id: Item UUID
            
        Returns:
            Wishlist entry
            
        Raises:
            HTTPException: If item doesn't exist
        """
        # Verify item exists
        item_query = select(Item).where(Item.id == item_id)
        item_result = await db.execute(item_query)
        if not item_result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Item not found"
            )
        
        # Check if already in wishlist
        existing_query = select(Wishlist).where(
            Wishlist.user_id == user_id,
            Wishlist.item_id == item_id
        )
        existing_result = await db.execute(existing_query)
        existing = existing_result.scalar_one_or_none()
        
        if existing:
            return existing
        
        # Create new wishlist entry
        wishlist_entry = Wishlist(user_id=user_id, item_id=item_id)
        db.add(wishlist_entry)
        await db.commit()
        await db.refresh(wishlist_entry)
        
        return wishlist_entry
    
    @staticmethod
    async def get_user_wishlist(
        db: AsyncSession,
        user_id: UUID
    ) -> List[Wishlist]:
        """
        Get user's wishlist with item details.
        
        Args:
            db: Database session
            user_id: User UUID
            
        Returns:
            List of wishlist entries with items
        """
        query = (
            select(Wishlist)
            .options(selectinload(Wishlist.item))
            .where(Wishlist.user_id == user_id)
            .order_by(Wishlist.created_at.desc())
        )
        
        result = await db.execute(query)
        return result.scalars().all()
    
    @staticmethod
    async def remove_from_wishlist(
        db: AsyncSession,
        user_id: UUID,
        item_id: UUID
    ) -> bool:
        """
        Remove an item from user's wishlist.
        
        Args:
            db: Database session
            user_id: User UUID
            item_id: Item UUID
            
        Returns:
            True if removed, False if not found
        """
        stmt = delete(Wishlist).where(
            Wishlist.user_id == user_id,
            Wishlist.item_id == item_id
        )
        
        result = await db.execute(stmt)
        await db.commit()
        
        return result.rowcount > 0
    
    @staticmethod
    async def clear_user_wishlist(db: AsyncSession, user_id: UUID) -> int:
        """
        Clear all items from user's wishlist.
        
        Args:
            db: Database session
            user_id: User UUID
            
        Returns:
            Number of items removed
        """
        stmt = delete(Wishlist).where(Wishlist.user_id == user_id)
        result = await db.execute(stmt)
        await db.commit()
        
        return result.rowcount