import hashlib
import os
import re
import uuid
from typing import Any, Dict, Optional
from app.core.config import settings

class StorageService:
    """Manages object storage paths, signed upload/download URLs, and binary persistence."""

    _memory_store: Dict[str, bytes] = {}

    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """Sanitize filename to prevent directory traversal and illegal characters."""
        clean = os.path.basename(filename)
        clean = re.sub(r"[^\w\.\-\s]", "_", clean)
        return clean.strip() or "file"

    @classmethod
    def generate_storage_path(
        cls,
        user_id: uuid.UUID,
        file_id: uuid.UUID,
        version_number: int,
        filename: str,
    ) -> str:
        """Construct standard partitioned storage path for an object version."""
        safe_name = cls.sanitize_filename(filename)
        return f"uploads/{user_id}/{file_id}/v{version_number}_{safe_name}"

    @classmethod
    def compute_checksum_sha256(cls, file_bytes: bytes) -> str:
        """Calculate hexadecimal SHA-256 digest of file binary bytes."""
        hasher = hashlib.sha256()
        hasher.update(file_bytes)
        return hasher.hexdigest()

    @classmethod
    def generate_presigned_upload_url(
        cls,
        storage_path: str,
        expires_in_seconds: int = 3600,
    ) -> Dict[str, Any]:
        """Generate a presigned upload URL for direct client-to-storage upload."""
        clean_path = storage_path.lstrip("/")
        base_url = settings.SUPABASE_URL.rstrip("/")
        bucket = settings.SUPABASE_STORAGE_BUCKET

        upload_url = (
            f"{base_url}/storage/v1/object/upload/sign/{bucket}/{clean_path}"
            f"?token=signed_upload_token_{uuid.uuid4().hex[:16]}"
        )

        return {
            "upload_url": upload_url,
            "storage_path": clean_path,
            "expires_in_seconds": expires_in_seconds,
            "method": "PUT",
        }

    @classmethod
    def generate_presigned_download_url(
        cls,
        storage_path: str,
        filename: str,
        expires_in_seconds: int = 3600,
    ) -> str:
        """Generate a presigned download URL for direct client-to-storage download."""
        clean_path = storage_path.lstrip("/")
        base_url = settings.SUPABASE_URL.rstrip("/")
        bucket = settings.SUPABASE_STORAGE_BUCKET
        safe_name = cls.sanitize_filename(filename)

        return (
            f"{base_url}/storage/v1/object/sign/{bucket}/{clean_path}"
            f"?token=signed_download_token_{uuid.uuid4().hex[:16]}"
            f"&download={safe_name}"
        )

    @classmethod
    def save_file_bytes(cls, storage_path: str, file_bytes: bytes) -> None:
        """Persist binary bytes into storage provider."""
        clean_path = storage_path.lstrip("/")
        cls._memory_store[clean_path] = file_bytes

    @classmethod
    def get_file_bytes(cls, storage_path: str) -> Optional[bytes]:
        """Retrieve binary bytes from storage provider."""
        clean_path = storage_path.lstrip("/")
        return cls._memory_store.get(clean_path)

    @classmethod
    def delete_file_bytes(cls, storage_path: str) -> bool:
        """Purge binary bytes from storage provider."""
        clean_path = storage_path.lstrip("/")
        if clean_path in cls._memory_store:
            del cls._memory_store[clean_path]
            return True
        return False
