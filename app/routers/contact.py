# app/routers/contact.py

"""
API routes for the Contact module.
Provides public and admin endpoints for contact message management.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from typing import List

from app.database import get_db
from app.schemas.contact import ContactCreate, ContactResponse, ContactUpdate
from app.services.contact_service import ContactService

# ----------------------------------------------------------------------------
# Router setup
# ----------------------------------------------------------------------------
# All routes in this file will be prefixed with "/contact"
# Example: POST /contact/, GET /contact/, DELETE /contact/{id}
router = APIRouter(prefix="/contact", tags=["Contact"])


# ============================================================================
# Public Endpoint → Submit a contact form
# ============================================================================
@router.post("/", response_model=ContactResponse, status_code=status.HTTP_201_CREATED)
async def submit_message(payload: ContactCreate, db: AsyncSession = Depends(get_db)):
    """
    Public endpoint:
    - Allows anyone to submit a new contact message.
    - Saves message in PostgreSQL (Neon).
    """
    # Pass validated data to service → returns ContactMessage ORM object
    return await ContactService.create_message(db, payload.dict())


# ============================================================================
# Admin Endpoints → Manage messages
# ============================================================================

@router.get("/", response_model=List[ContactResponse])
async def list_messages(db: AsyncSession = Depends(get_db)):
    """
    Admin endpoint:
    - Retrieve all contact messages.
    - Ordered by created_at (newest first).
    """
    return await ContactService.list_messages(db)


@router.get("/{message_id}", response_model=ContactResponse)
async def get_message(message_id: UUID, db: AsyncSession = Depends(get_db)):
    """
    Admin endpoint:
    - Retrieve a single message by its ID (UUID).
    """
    message = await ContactService.get_message(db, message_id)
    if not message:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Message not found"
        )
    return message


@router.put("/{message_id}", response_model=ContactResponse)
async def update_message(message_id: UUID, payload: ContactUpdate, db: AsyncSession = Depends(get_db)):
    """
    Admin endpoint:
    - Update a contact message by ID.
    - Supports partial updates (only send the fields you want to change).
    """
    updated = await ContactService.update_message(
        db,
        message_id,
        payload.dict(exclude_unset=True)  # ignore missing fields
    )
    if not updated:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Message not found"
        )
    return updated


@router.delete("/{message_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_message(message_id: UUID, db: AsyncSession = Depends(get_db)):
    """
    Admin endpoint:
    - Delete a contact message by ID.
    """
    deleted = await ContactService.delete_message(db, message_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Message not found"
        )
    return None


# ============================================================================
# Bulk Delete Endpoint → Clear all messages
# ============================================================================
@router.delete("/", status_code=status.HTTP_204_NO_CONTENT)
async def delete_all_messages(db: AsyncSession = Depends(get_db)):
    """
    Admin endpoint:
    - Delete ALL contact messages from the database.
    - ⚠️ This action is permanent and cannot be undone.
    """
    await ContactService.delete_all_messages(db)
    return None
