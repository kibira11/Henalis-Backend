"""
Service layer for Contact module.
Handles business logic for contact message CRUD operations.
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, update
from uuid import UUID

from app.models.contact import ContactMessage


class ContactService:
    # ============================================================
    # CREATE → Add new contact message
    # ============================================================
    @staticmethod
    async def create_message(db: AsyncSession, data: dict):
        """
        Create a new contact message and save to database.
        """
        new_message = ContactMessage(**data)  # Map dict → model
        db.add(new_message)
        await db.commit()
        await db.refresh(new_message)  # Refresh to return with ID + created_at
        return new_message

    # ============================================================
    # READ → List all messages
    # ============================================================
    @staticmethod
    async def list_messages(db: AsyncSession):
        """
        Return all messages ordered by created_at (newest first).
        """
        result = await db.execute(select(ContactMessage).order_by(ContactMessage.created_at.desc()))
        return result.scalars().all()

    # ============================================================
    # READ → Get single message by ID
    # ============================================================
    @staticmethod
    async def get_message(db: AsyncSession, message_id: UUID):
        """
        Fetch a single message by UUID.
        """
        result = await db.execute(select(ContactMessage).where(ContactMessage.id == message_id))
        return result.scalars().first()

    # ============================================================
    # UPDATE → Update message by ID
    # ============================================================
    @staticmethod
    async def update_message(db: AsyncSession, message_id: UUID, data: dict):
        """
        Update a message by ID with partial fields.
        """
        # Run update query
        await db.execute(
            update(ContactMessage)
            .where(ContactMessage.id == message_id)
            .values(**data)
        )
        await db.commit()

        # Fetch updated message
        result = await db.execute(select(ContactMessage).where(ContactMessage.id == message_id))
        return result.scalars().first()

    # ============================================================
    # DELETE → Delete one message
    # ============================================================
    @staticmethod
    async def delete_message(db: AsyncSession, message_id: UUID):
        """
        Delete a message by ID.
        Returns True if deleted, False if not found.
        """
        result = await db.execute(select(ContactMessage).where(ContactMessage.id == message_id))
        message = result.scalars().first()

        if not message:
            return False

        await db.delete(message)
        await db.commit()
        return True

    # ============================================================
    # DELETE ALL → Clear all messages
    # ============================================================
    @staticmethod
    async def delete_all_messages(db: AsyncSession):
        """
        Bulk delete: remove ALL contact messages.
        Use carefully → this action cannot be undone.
        """
        await db.execute(delete(ContactMessage))  # Delete all rows
        await db.commit()
        return True
