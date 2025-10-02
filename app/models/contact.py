# app/models/contact.py

"""
SQLAlchemy model for the Contact module.
Defines the ContactMessage table for storing user-submitted messages.
"""

from sqlalchemy import Column, String, Text, DateTime, Enum
from sqlalchemy.dialects.postgresql import UUID  # Native Postgres UUID type
from sqlalchemy.sql import func  # For auto timestamp
from app.database import Base
import uuid
import enum


class ContactSubject(str, enum.Enum):
    """
    Enum for contact message subjects.
    This restricts the `subject` field to fixed values only.
    """
    GENERAL_INQUIRY = "General Inquiry"
    PRODUCT_INFO = "Product Information"
    ORDER_STATUS = "Order Status"
    DELIVERY_INFO = "Delivery Information"
    WARRANTY_CLAIM = "Warranty Claim"
    CUSTOM_FURNITURE = "Custom Furniture"
    FEEDBACK = "Feedback"


class ContactMessage(Base):
    """
    Contact message model for storing submissions from users.
    Maps to the `contact_messages` table in PostgreSQL.
    """
    __tablename__ = "contact_messages"

    # Primary Key (UUID for global uniqueness)
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Full name of the user (required)
    full_name = Column(String(255), nullable=False)

    # Email address (required, indexed for faster queries)
    email = Column(String(255), nullable=False, index=True)

    # Phone number (optional)
    phone = Column(String(20), nullable=True)

    # Subject of inquiry (restricted to ContactSubject Enum)
    subject = Column(Enum(ContactSubject), nullable=False)

    # Message body (required text field)
    message = Column(Text, nullable=False)

    # Auto timestamp (set to NOW() on insert)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    def __repr__(self):
        return f"<ContactMessage(id={self.id}, subject={self.subject}, email={self.email})>"
