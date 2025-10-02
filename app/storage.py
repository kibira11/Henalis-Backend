# app/storage.py
"""
Local Storage helper module.
Replaces Supabase with simple filesystem-based storage.
Uploads are saved to `app/static/uploads/...`
"""

import os
import uuid
from pathlib import Path
from fastapi import UploadFile, HTTPException, status

# Define the base upload directory (inside project)
UPLOAD_DIR = Path("app/static/uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)  # ensure directory exists


class LocalStorage:
    """Simple storage backend using local filesystem."""

    async def upload_file(self, file: UploadFile, folder: str = "items", filename: str = None):
        """
        Save an uploaded file to the local filesystem.

        Args:
            file: The FastAPI UploadFile object.
            folder: Subfolder within `uploads` (e.g., 'items', 'users').
            filename: Optional custom filename (auto-generate UUID if None).

        Returns:
            Tuple: (absolute file path, public URL)
        """
        # Generate a unique filename if not provided
        if filename is None:
            ext = os.path.splitext(file.filename)[1] if file.filename else ""
            filename = f"{uuid.uuid4()}{ext}"

        # Create folder path if it doesn't exist
        folder_path = UPLOAD_DIR / folder
        folder_path.mkdir(parents=True, exist_ok=True)

        # Full path where file will be saved
        file_path = folder_path / filename

        try:
            # Read file content
            content = await file.read()

            # Save file locally
            with open(file_path, "wb") as f:
                f.write(content)

            # Construct public URL (served via /static)
            public_url = f"/static/uploads/{folder}/{filename}"
            return str(file_path), public_url

        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to save file: {str(e)}"
            )

    async def delete_file(self, storage_path: str) -> bool:
        """
        Delete a file from local storage.

        Args:
            storage_path: The absolute file path.

        Returns:
            True if deleted (or missing), raises error if failed.
        """
        try:
            os.remove(storage_path)
            return True
        except FileNotFoundError:
            # Ignore if already deleted
            return True
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to delete file: {str(e)}"
            )


# Global storage instance
storage = LocalStorage()
