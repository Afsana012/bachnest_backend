"""Storage provider protocol and local filesystem storage implementation."""

import os
import uuid
from typing import Protocol


class StorageProvider(Protocol):
    async def upload(self, file_content: bytes, filename: str, content_type: str) -> str:
        ...

    async def delete(self, file_url: str) -> bool:
        ...


class LocalStorageProvider:
    def __init__(self, base_dir: str = "uploads"):
        self.base_dir = base_dir
        os.makedirs(self.base_dir, exist_ok=True)

    async def upload(self, file_content: bytes, filename: str, content_type: str) -> str:
        ext = filename.split(".")[-1] if "." in filename else "bin"
        unique_name = f"{uuid.uuid4().hex}.{ext}"
        target_path = os.path.join(self.base_dir, unique_name)
        with open(target_path, "wb") as f:
            f.write(file_content)
        return f"/uploads/{unique_name}"

    async def delete(self, file_url: str) -> bool:
        filename = os.path.basename(file_url)
        target_path = os.path.join(self.base_dir, filename)
        if os.path.exists(target_path):
            os.remove(target_path)
            return True
        return False
