"""Test Cloudflare R2 storage connection and upload."""

import asyncio
import boto3
from botocore.config import Config

account_id = "7b2b503530b54d9083f1672a82640ade"
access_key = "b8cd4cd7a066d781bc0a23ccd79b99d7"
secret_key = "ded3280c0e08f0bcbdec56e151a76d7b94573e519cfd9025190380d55dd277b7"
bucket_name = "bachnest"
public_domain = "https://pub-7b2b503530b54d9083f1672a82640ade.r2.dev"
endpoint_url = f"https://{account_id}.r2.cloudflarestorage.com"

print(f"Testing Cloudflare R2 Endpoint: {endpoint_url}")

s3_client = boto3.client(
    "s3",
    endpoint_url=endpoint_url,
    aws_access_key_id=access_key,
    aws_secret_access_key=secret_key,
    config=Config(signature_version="s3v4"),
    region_name="auto",
)

try:
    # Test bucket listing or head bucket
    print(f"Checking bucket '{bucket_name}'...")
    s3_client.head_bucket(Bucket=bucket_name)
    print(f"[OK] Bucket '{bucket_name}' accessible!")

    # Test file upload
    test_key = "tests/connection_test.txt"
    test_data = b"BachNest Cloudflare R2 Storage Connected Successfully!"
    print(f"Uploading test object '{test_key}'...")
    s3_client.put_object(
        Bucket=bucket_name,
        Key=test_key,
        Body=test_data,
        ContentType="text/plain",
    )
    print(f"[OK] Test object uploaded successfully!")
    print(f"[OK] Public URL: {public_domain}/{test_key}")

except Exception as e:
    print(f"[ERROR] Cloudflare R2 connection failed: {e}")
