# app/schemas/contact.py

"""
Pydantic schemas for request/response validation in the Contact module.
"""

from pydantic import BaseModel, EmailStr, Field, ConfigDict
from typing import Optional
from uuid import UUID
from datetime import datetime
from app.models.contact import ContactSubject


class ContactBase(BaseModel):
    """
    Base schema for contact messages.
    Shared by both create and response schemas.
    """
    full_name: str = Field(..., min_length=1, max_length=255, examples=["John Doe"])
    email: EmailStr = Field(..., examples=["johndoe@example.com"])
    phone: Optional[str] = Field(None, min_length=7, max_length=20, examples=["+123456789"])
    subject: ContactSubject  # Must match one of the enum values
    message: str = Field(..., min_length=5, max_length=2000, examples=["I would like to know more about this product."])


class ContactCreate(ContactBase):
    """
    Schema for creating a new contact message (public form).
    Inherits from ContactBase, so no extra fields are required.
    """
    pass


class ContactUpdate(BaseModel):
    """
    Schema for updating an existing contact message (admin only).
    All fields are optional here (partial update).
    """
    full_name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    subject: Optional[ContactSubject] = None
    message: Optional[str] = None


class ContactResponse(ContactBase):
    """
    Schema for returning contact messages in API responses.
    Includes extra metadata fields: id and created_at.
    """
    id: UUID
    created_at: datetime

    # Enables mapping directly from SQLAlchemy ORM objects
    model_config = ConfigDict(from_attributes=True)
