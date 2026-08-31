"""Cloudflare R2 / S3-compatible object storage provider."""

import os
import uuid
import boto3
from botocore.config import Config

from app.core.config import settings


class R2StorageProvider:
    def __init__(
        self,
        endpoint_url: str = "",
        access_key: str = "",
        secret_key: str = "",
        bucket_name: str = "bachnest",
        public_domain: str = "https://pub-7b2b503530b54d9083f1672a82640ade.r2.dev",
    ):
        self.endpoint_url = endpoint_url or getattr(settings, "STORAGE_ENDPOINT_URL", "")
        self.access_key = access_key or settings.STORAGE_ACCESS_KEY
        self.secret_key = secret_key or settings.STORAGE_SECRET_KEY
        self.bucket_name = bucket_name or settings.STORAGE_BUCKET or "bachnest"
        self.public_domain = (public_domain or getattr(settings, "STORAGE_PUBLIC_DOMAIN", "")).rstrip("/")

        self.client = boto3.client(
            "s3",
            endpoint_url=self.endpoint_url,
            aws_access_key_id=self.access_key,
            aws_secret_access_key=self.secret_key,
            config=Config(signature_version="s3v4"),
            region_name="auto",
        )

    async def upload(self, file_content: bytes, filename: str, content_type: str = "image/jpeg", folder: str = "properties") -> str:
        """Upload file bytes to Cloudflare R2 bucket and return public URL."""
        ext = filename.split(".")[-1] if "." in filename else "jpg"
        unique_key = f"{folder}/{uuid.uuid4().hex}.{ext}"

        self.client.put_object(
            Bucket=self.bucket_name,
            Key=unique_key,
            Body=file_content,
            ContentType=content_type,
        )

        if self.public_domain:
            return f"{self.public_domain}/{unique_key}"
        return f"{self.endpoint_url}/{self.bucket_name}/{unique_key}"

    async def delete(self, file_url: str) -> bool:
        """Delete an object from Cloudflare R2 by URL."""
        try:
            # Extract key from URL
            if self.public_domain and file_url.startswith(self.public_domain):
                key = file_url[len(self.public_domain):].lstrip("/")
            else:
                key = file_url.split(f"/{self.bucket_name}/")[-1].lstrip("/")

            self.client.delete_object(Bucket=self.bucket_name, Key=key)
            return True
        except Exception:
            return False

    async def create_signed_url(self, key: str, expires_in: int = 3600) -> str:
        """Generate a short-lived presigned URL for private documents (KYC)."""
        return self.client.generate_presigned_url(
            "get_object",
            Params={"Bucket": self.bucket_name, "Key": key},
            ExpiresIn=expires_in,
        )
