"""
File storage, abstracted behind a simple interface so the backing store
can be swapped between local disk (development) and Cloudinary
(production) purely via the STORAGE_PROVIDER environment variable —
no changes needed anywhere else in the app.
"""
import os
import uuid
from abc import ABC, abstractmethod

from app.config import settings


class StorageService(ABC):
    @abstractmethod
    def save(self, file_bytes: bytes, original_filename: str, user_id: int) -> str:
        """Persists the file and returns a URL/path the frontend can use to reference it."""


class LocalStorageService(StorageService):
    """Stores files on local disk under UPLOAD_DIR/{user_id}/. Suitable for
    development; in production this directory should be a persistent volume,
    or STORAGE_PROVIDER should be switched to "cloudinary"."""

    def save(self, file_bytes: bytes, original_filename: str, user_id: int) -> str:
        ext = os.path.splitext(original_filename)[1].lower()
        stored_name = f"{uuid.uuid4().hex}{ext}"

        user_dir = os.path.join(settings.UPLOAD_DIR, str(user_id))
        os.makedirs(user_dir, exist_ok=True)

        absolute_path = os.path.join(user_dir, stored_name)
        with open(absolute_path, "wb") as f:
            f.write(file_bytes)

        # Relative URL the frontend/static file server can resolve.
        return f"/uploads/{user_id}/{stored_name}"


class CloudinaryStorageService(StorageService):
    """Uploads files to Cloudinary. Requires CLOUDINARY_CLOUD_NAME,
    CLOUDINARY_API_KEY, and CLOUDINARY_API_SECRET to be set."""

    def __init__(self):
        import cloudinary

        cloudinary.config(
            cloud_name=settings.CLOUDINARY_CLOUD_NAME,
            api_key=settings.CLOUDINARY_API_KEY,
            api_secret=settings.CLOUDINARY_API_SECRET,
        )

    def save(self, file_bytes: bytes, original_filename: str, user_id: int) -> str:
        import cloudinary.uploader

        result = cloudinary.uploader.upload(
            file_bytes,
            folder=f"expense_manager/{user_id}",
            resource_type="auto",
        )
        return result["secure_url"]


def get_storage_service() -> StorageService:
    if settings.STORAGE_PROVIDER == "cloudinary":
        return CloudinaryStorageService()
    return LocalStorageService()
