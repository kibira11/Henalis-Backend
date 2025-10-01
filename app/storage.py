# app/storage.py

"""
Supabase Storage helper module.
Provides async functions for uploading, deleting, and managing files in Supabase Storage.
"""

import httpx
from typing import Optional
from fastapi import UploadFile, HTTPException, status
from app.config import settings
import uuid
import os


class SupabaseStorage:
    """Helper class for interacting with Supabase Storage."""

    def __init__(self):
        self.base_url = f"{settings.supabase_url}/storage/v1"
        self.bucket = settings.supabase_storage_bucket
        self.service_key = settings.supabase_service_role_key

    def _get_headers(self) -> dict:
        """Get headers for Supabase Storage API requests."""
        return {
            "Authorization": f"Bearer {self.service_key}",
            "apikey": self.service_key,
        }

    async def upload_file(
        self,
        file: UploadFile,
        folder: str = "items",
        filename: Optional[str] = None,
    ) -> tuple[str, str]:
        """
        Upload a file to Supabase Storage.

        Args:
            file: The file to upload
            folder: The folder path within the bucket
            filename: Optional custom filename (will generate UUID if not provided)

        Returns:
            Tuple of (storage_path, public_url)
        """
        # Generate unique filename if not provided
        if filename is None:
            ext = os.path.splitext(file.filename)[1] if file.filename else ""
            filename = f"{uuid.uuid4()}{ext}"

        storage_path = f"{folder}/{filename}"

        # Read file content
        content = await file.read()

        # Upload to Supabase (must use PUT)
        upload_url = f"{self.base_url}/object/{self.bucket}/{storage_path}"

        try:
            async with httpx.AsyncClient() as client:
                response = await client.put(
                    upload_url,
                    headers={
                        **self._get_headers(),
                        "Content-Type": file.content_type
                        or "application/octet-stream",
                    },
                    content=content,
                    timeout=30.0,
                )

                if response.status_code not in [200, 201]:
                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail=f"Failed to upload file: {response.text}",
                    )

                # Construct public URL
                public_url = self.get_public_url(storage_path)
                return storage_path, public_url

        except httpx.HTTPError as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Storage upload error: {str(e)}",
            )

    async def delete_file(self, storage_path: str) -> bool:
        """
        Delete a file from Supabase Storage.
        """
        delete_url = f"{self.base_url}/object/{self.bucket}/{storage_path}"

        try:
            async with httpx.AsyncClient() as client:
                response = await client.delete(
                    delete_url,
                    headers=self._get_headers(),
                    timeout=10.0,
                )

                if response.status_code not in [200, 204]:
                    if response.status_code == 404:
                        return True  # ignore if file missing
                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail=f"Failed to delete file: {response.text}",
                    )

                return True

        except httpx.HTTPError as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Storage deletion error: {str(e)}",
            )

    def get_public_url(self, storage_path: str) -> str:
        """
        Get the public URL for a file in Supabase Storage.
        """
        return f"{settings.supabase_url}/storage/v1/object/public/{self.bucket}/{storage_path}"

    async def get_signed_url(
        self, storage_path: str, expires_in: int = 3600
    ) -> str:
        """
        Get a signed (temporary) URL for a file.
        Useful for private buckets.
        """
        sign_url = f"{self.base_url}/object/sign/{self.bucket}/{storage_path}"

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    sign_url,
                    headers=self._get_headers(),
                    json={"expiresIn": expires_in},
                    timeout=10.0,
                )

                if response.status_code != 200:
                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail=f"Failed to generate signed URL: {response.text}",
                    )

                data = response.json()
                signed_path = data.get("signedURL")

                if not signed_path:
                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail="No signed URL returned from storage",
                    )

                return f"{settings.supabase_url}/storage/v1{signed_path}"

        except httpx.HTTPError as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Storage signed URL error: {str(e)}",
            )


# Global storage instance
storage = SupabaseStorage()
