# app/schemas/subscriber.py

from pydantic import BaseModel, EmailStr, Field
from datetime import datetime
from uuid import UUID
from typing import Optional, List


# ============================================================================
# Base Schema
# ============================================================================

class SubscriberBase(BaseModel):
    email: EmailStr


# ============================================================================
# Create Schema
# ============================================================================

class SubscriberCreate(SubscriberBase):
    pass


# ============================================================================
# Update Schema
# ============================================================================

class SubscriberUpdate(BaseModel):
    """Schema for updating subscriber info (admin only)."""
    email: Optional[EmailStr] = None
    is_active: Optional[bool] = None


# ============================================================================
# Response Schema
# ============================================================================

class SubscriberResponse(SubscriberBase):
    id: UUID
    created_at: datetime
    is_active: bool = True  # ✅ better to expose this

    class Config:
        from_attributes = True  # Pydantic v2 replacement for orm_mode


# ============================================================================
# Bulk Delete Schema
# ============================================================================

class BulkDeleteRequest(BaseModel):
    """Schema for bulk delete operations."""
    ids: List[UUID] = Field(..., examples=[["uuid1", "uuid2"]])
