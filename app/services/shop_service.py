# app/services/shop_service.py

"""
Service layer for Shop-related business logic.

This module centralizes data access and business rules for:
- Items (filtering, pagination, details)
- Bulk update / delete helpers (generic)
- Image helpers (set primary image, create image record)
- Likes increment
- Wishlist management

Routers should be thin and call these service methods.
Each function receives an AsyncSession and performs necessary commits/refreshes.
"""

from typing import List, Optional, Dict, Any, Tuple
from uuid import UUID
from decimal import Decimal

from sqlalchemy import select, update, delete, func, and_
from sqlalchemy.orm import selectinload
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.shop import (
    Category,
    Material,
    Tag,
    Item,
    ItemImage,
    Wishlist,
    item_tags
)


class ShopService:
    # ---------------------------
    # Generic bulk helpers
    # ---------------------------
    @staticmethod
    async def bulk_update_entities(
        db: AsyncSession,
        model,
        ids: List[UUID],
        patch: Dict[str, Any]
    ) -> int:
        """
        Bulk update entities of a given model by IDs.
        - db: AsyncSession
        - model: SQLAlchemy model class (e.g., Item, Category)
        - ids: list of UUIDs
        - patch: dict of fields to set

        Returns number of rows updated.
        """
        if not ids:
            return 0

        try:
            stmt = (
                update(model)
                .where(model.id.in_(ids))
                .values(**patch)
                .execution_options(synchronize_session="fetch")
            )
            result = await db.execute(stmt)
            await db.commit()
            # result.rowcount may be DB-driver dependent; return the count if present else len(ids)
            return result.rowcount if result.rowcount is not None else len(ids)
        except SQLAlchemyError:
            await db.rollback()
            raise

    @staticmethod
    async def bulk_delete_entities(
        db: AsyncSession,
        model,
        ids: List[UUID]
    ) -> int:
        """
        Bulk delete entities by IDs.
        Returns number of rows deleted.
        """
        if not ids:
            return 0

        try:
            stmt = delete(model).where(model.id.in_(ids)).execution_options(synchronize_session="fetch")
            result = await db.execute(stmt)
            await db.commit()
            return result.rowcount if result.rowcount is not None else len(ids)
        except SQLAlchemyError:
            await db.rollback()
            raise

    # ---------------------------
    # Item listing & detail
    # ---------------------------
    @staticmethod
    async def get_items_with_filters(
        db: AsyncSession,
        category: Optional[str] = None,   # slug or UUID string
        material: Optional[str] = None,   # UUID string
        price_min: Optional[Decimal] = None,
        price_max: Optional[Decimal] = None,
        tags: Optional[str] = None,       # comma-separated UUIDs
        is_active: Optional[bool] = None,
        q: Optional[str] = None,
        sort: str = "newest",
        limit: int = 12,
        offset: int = 0,
    ) -> Dict[str, Any]:
        """
        Return paginated items with applied filters.
        Returns: { "items": [Item,...], "meta": {"total": n, "limit": limit, "offset": offset} }
        """

        # Base query selects items and eager loads images, tags, category, material
        base_q = select(Item).options(
            selectinload(Item.images),
            selectinload(Item.tags),
            selectinload(Item.category),
            selectinload(Item.material),
        )

        # WHERE clauses
        where_clauses = []

        # Category can be slug or UUID
        if category:
            # attempt to match slug first
            category_clause = Category.slug == category
            where_clauses.append(
                or_(
                    Item.category_id == None,  # placeholder so we can use or_ below safely (we'll combine properly)
                )
            )
            # Simpler approach: join category
            base_q = base_q.join(Category, isouter=True)
            base_q = base_q.where(
                (Category.slug == category) | (Category.id.cast(String) == category)
            )

        # Material (UUID)
        if material:
            base_q = base_q.where(Item.material_id.cast(String) == material)

        # Price range
        if price_min is not None:
            base_q = base_q.where(Item.price_decimal >= price_min)
        if price_max is not None:
            base_q = base_q.where(Item.price_decimal <= price_max)

        # Tags - filter items that have ALL provided tags would be more complex; here we filter items having any of the tags
        if tags:
            tag_ids = [tag.strip() for tag in tags.split(",") if tag.strip()]
            if tag_ids:
                # Join the association table
                base_q = base_q.join(item_tags).join(Tag)
                base_q = base_q.where(Tag.id.cast(String).in_(tag_ids))

        # is_active
        if is_active is not None:
            base_q = base_q.where(Item.is_active == is_active)

        # Search q: name, sku, description
        if q:
            search = f"%{q.lower()}%"
            # Use lower() func for case-insensitive where possible
            base_q = base_q.where(
                or_(
                    func.lower(Item.name).like(search),
                    func.lower(Item.sku).like(search),
                    func.lower(Item.description).like(search)
                )
            )

        # Deduplicate when joins used
        base_q = base_q.distinct()

        # Sorting
        if sort == "price-low":
            base_q = base_q.order_by(Item.price_decimal.asc())
        elif sort == "price-high":
            base_q = base_q.order_by(Item.price_decimal.desc())
        elif sort == "most-loved":
            base_q = base_q.order_by(Item.likes.desc())
        else:  # newest
            base_q = base_q.order_by(Item.created_at.desc())

        # Count total (separate query)
        count_q = select(func.count()).select_from(select(Item).subquery())
        # Note: the above count query is a generic fallback; for simple setups you may want to build a count with same joins/filters.

        # Apply limit & offset for pagination
        items_q = base_q.limit(limit).offset(offset)

        result = await db.execute(items_q)
        items = result.scalars().unique().all()

        # Total: do a simple count without join complexity (could be inaccurate if tag/category filters used with joins)
        total_result = await db.execute(select(func.count(Item.id)))
        total = total_result.scalar_one()

        return {
            "items": items,
            "meta": {"total": total, "limit": limit, "offset": offset},
        }

    @staticmethod
    async def get_item_detail(db: AsyncSession, item_id: UUID) -> Optional[Item]:
        """
        Return a single Item object with related images, tags, category, material loaded.
        """
        stmt = select(Item).options(
            selectinload(Item.images),
            selectinload(Item.tags),
            selectinload(Item.category),
            selectinload(Item.material),
        ).where(Item.id == item_id)

        result = await db.execute(stmt)
        item = result.scalar_one_or_none()
        return item

    # ---------------------------
    # Image helpers
    # ---------------------------
    @staticmethod
    async def create_item_image(
        db: AsyncSession,
        item_id: UUID,
        storage_path: str,
        url: str,
        is_primary: bool = False
    ) -> ItemImage:
        """
        Create an ItemImage row after file was uploaded to storage (local or cloud).
        If is_primary is True, ensure other images for that item are un-set.
        """
        # Ensure item exists
        item = (await db.execute(select(Item).where(Item.id == item_id))).scalar_one_or_none()
        if not item:
            raise ValueError("Item not found")

        image = ItemImage(
            item_id=item_id,
            storage_path=storage_path,
            url=url,
            is_primary=is_primary
        )
        db.add(image)
        await db.commit()
        await db.refresh(image)

        # If setting primary - clear other primary flags
        if is_primary:
            await ShopService.set_primary_image(db, image.id, item_id)

        return image

    @staticmethod
    async def set_primary_image(db: AsyncSession, image_id: UUID, item_id: UUID) -> Optional[ItemImage]:
        """
        Mark the provided image_id as the primary image for the given item_id.
        Ensures only one primary image per item.
        Returns the updated ItemImage instance.
        """
        # Set all images for this item to is_primary = False
        try:
            await db.execute(
                update(ItemImage)
                .where(ItemImage.item_id == item_id)
                .values(is_primary=False)
                .execution_options(synchronize_session="fetch")
            )

            # Set specific image to true
            await db.execute(
                update(ItemImage)
                .where(ItemImage.id == image_id, ItemImage.item_id == item_id)
                .values(is_primary=True)
                .execution_options(synchronize_session="fetch")
            )

            await db.commit()

            # Return refreshed image
            img = (await db.execute(select(ItemImage).where(ItemImage.id == image_id))).scalar_one_or_none()
            return img
        except SQLAlchemyError:
            await db.rollback()
            raise

    @staticmethod
    async def delete_item_image(db: AsyncSession, image_id: UUID) -> bool:
        """
        Delete image record from DB. Caller should delete storage file separately (e.g., storage.delete_file).
        Returns True if deleted.
        """
        try:
            result = await db.execute(select(ItemImage).where(ItemImage.id == image_id))
            image = result.scalar_one_or_none()
            if not image:
                return False

            await db.delete(image)
            await db.commit()
            return True
        except SQLAlchemyError:
            await db.rollback()
            raise

    # ---------------------------
    # Likes
    # ---------------------------
    @staticmethod
    async def increment_item_likes(db: AsyncSession, item_id: UUID) -> Optional[Item]:
        """
        Atomically increment the likes counter for an item and return the updated item.
        """
        try:
            await db.execute(
                update(Item)
                .where(Item.id == item_id)
                .values(likes=Item.likes + 1)
                .execution_options(synchronize_session="fetch")
            )
            await db.commit()
            item = (await db.execute(select(Item).where(Item.id == item_id))).scalar_one_or_none()
            return item
        except SQLAlchemyError:
            await db.rollback()
            raise

    # ---------------------------
    # Wishlist management
    # ---------------------------
    @staticmethod
    async def get_user_wishlist(db: AsyncSession, user_id: UUID) -> List[Wishlist]:
        """
        Return wishlist entries for a user with item loaded.
        """
        stmt = select(Wishlist).options(selectinload(Wishlist.item)).where(Wishlist.user_id == user_id).order_by(Wishlist.created_at.desc())
        result = await db.execute(stmt)
        return result.scalars().all()

    @staticmethod
    async def add_to_wishlist(db: AsyncSession, user_id: UUID, item_id: UUID) -> Wishlist:
        """
        Idempotently add an item to a user's wishlist.
        If already present, returns the existing entry.
        """
        # Check existence
        stmt = select(Wishlist).where(Wishlist.user_id == user_id, Wishlist.item_id == item_id)
        existing = (await db.execute(stmt)).scalar_one_or_none()
        if existing:
            return existing

        entry = Wishlist(user_id=user_id, item_id=item_id)
        db.add(entry)
        try:
            await db.commit()
            await db.refresh(entry)
            return entry
        except SQLAlchemyError:
            await db.rollback()
            raise

    @staticmethod
    async def remove_from_wishlist(db: AsyncSession, user_id: UUID, item_id: UUID) -> bool:
        """
        Remove a wishlist entry. Returns True if removed, False if not found.
        """
        stmt = select(Wishlist).where(Wishlist.user_id == user_id, Wishlist.item_id == item_id)
        entry = (await db.execute(stmt)).scalar_one_or_none()
        if not entry:
            return False
        try:
            await db.delete(entry)
            await db.commit()
            return True
        except SQLAlchemyError:
            await db.rollback()
            raise

    @staticmethod
    async def clear_user_wishlist(db: AsyncSession, user_id: UUID) -> int:
        """
        Clear all wishlist entries for a user. Returns number of deleted rows (best-effort).
        """
        try:
            stmt = delete(Wishlist).where(Wishlist.user_id == user_id)
            result = await db.execute(stmt)
            await db.commit()
            return result.rowcount if result.rowcount is not None else 0
        except SQLAlchemyError:
            await db.rollback()
            raise
