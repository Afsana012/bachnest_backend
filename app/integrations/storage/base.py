"""Storage factory providing the active storage provider instance."""

from typing import Protocol
from app.core.config import settings
from app.integrations.storage.local_storage import LocalStorageProvider
from app.integrations.storage.r2_storage import R2StorageProvider


class StorageProvider(Protocol):
    async def upload(self, file_content: bytes, filename: str, content_type: str = "image/jpeg", folder: str = "properties") -> str:
        ...

    async def delete(self, file_url: str) -> bool:
        ...


def get_storage_provider():
    """Return configured storage provider."""
    if settings.STORAGE_PROVIDER in ("r2", "s3"):
        return R2StorageProvider()
    return LocalStorageProvider(base_dir=settings.STORAGE_LOCAL_DIR)
