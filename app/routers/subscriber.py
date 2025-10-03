# app/routers/subscriber.py

"""
Subscribers API routes (Stay Updated).
Allows public users to subscribe with their email,
and admin-only endpoints to list, update, and delete subscribers.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
from uuid import UUID

from app.database import get_db
from app.dependencies import get_current_admin
from app.models.subscriber import Subscriber
from app.schemas.subscriber import (
    SubscriberCreate, SubscriberUpdate, SubscriberResponse,
    BulkDeleteRequest
)

router = APIRouter(prefix="/subscribers", tags=["Subscribers"])

# ============================================================================
# Public: Subscribe
# ============================================================================

@router.post("/", response_model=SubscriberResponse, status_code=201)
async def subscribe(
    subscriber: SubscriberCreate,
    db: AsyncSession = Depends(get_db),
):
    """
    Public endpoint to subscribe with an email address.
    """
    # Check if email already exists
    result = await db.execute(select(Subscriber).where(Subscriber.email == subscriber.email))
    existing = result.scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=400, detail="Email already subscribed")

    db_subscriber = Subscriber(email=subscriber.email)
    db.add(db_subscriber)
    await db.commit()
    await db.refresh(db_subscriber)
    return db_subscriber


# ============================================================================
# Admin: List Subscribers
# ============================================================================

@router.get("/", response_model=List[SubscriberResponse])
async def list_subscribers(
    q: Optional[str] = Query(None, description="Search by email"),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(get_current_admin),  # ✅ admin only
):
    """
    List all subscribers with optional email search and pagination (admin only).
    """
    query = select(Subscriber)
    if q:
        query = query.where(Subscriber.email.ilike(f"%{q}%"))
    query = query.order_by(Subscriber.created_at.desc()).limit(limit).offset(offset)

    result = await db.execute(query)
    return result.scalars().all()


# ============================================================================
# Admin: Update Subscriber
# ============================================================================

@router.patch("/{subscriber_id}", response_model=SubscriberResponse)
async def update_subscriber(
    subscriber_id: UUID,
    update_data: SubscriberUpdate,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(get_current_admin),
):
    """
    Update a subscriber's details (admin only).
    Example: deactivate a subscriber.
    """
    result = await db.execute(select(Subscriber).where(Subscriber.id == subscriber_id))
    subscriber = result.scalar_one_or_none()
    if not subscriber:
        raise HTTPException(status_code=404, detail="Subscriber not found")

    for field, value in update_data.model_dump(exclude_unset=True).items():
        setattr(subscriber, field, value)

    await db.commit()
    await db.refresh(subscriber)
    return subscriber


# ============================================================================
# Admin: Delete Subscriber
# ============================================================================

@router.delete("/{subscriber_id}", status_code=204)
async def delete_subscriber(
    subscriber_id: UUID,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(get_current_admin),
):
    """
    Delete a single subscriber by ID (admin only).
    """
    result = await db.execute(select(Subscriber).where(Subscriber.id == subscriber_id))
    subscriber = result.scalar_one_or_none()
    if not subscriber:
        raise HTTPException(status_code=404, detail="Subscriber not found")

    await db.delete(subscriber)
    await db.commit()


# ============================================================================
# Admin: Bulk Delete
# ============================================================================

@router.delete("/", response_model=dict)
async def bulk_delete_subscribers(
    bulk_request: BulkDeleteRequest,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(get_current_admin),
):
    """
    Bulk delete subscribers by IDs (admin only).
    """
    deleted = 0
    for subscriber_id in bulk_request.ids:
        result = await db.execute(select(Subscriber).where(Subscriber.id == subscriber_id))
        subscriber = result.scalar_one_or_none()
        if subscriber:
            await db.delete(subscriber)
            deleted += 1

    await db.commit()
    return {"deleted": deleted}
