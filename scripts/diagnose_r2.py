"""Diagnose SSL connection to Cloudflare R2."""

import httpx

url = "https://7b2b503530b54d9083f1672a82640ade.r2.cloudflarestorage.com"
print(f"Testing HTTPS GET to {url} with httpx...")

try:
    res = httpx.get(url, timeout=10.0)
    print(f"Status Code: {res.status_code}")
    print(f"Response: {res.text[:200]}")
except Exception as e:
    print(f"httpx error: {e}")

public_url = "https://pub-7b2b503530b54d9083f1672a82640ade.r2.dev"
print(f"\nTesting Public Domain: {public_url}...")
try:
    res = httpx.get(public_url, timeout=10.0)
    print(f"Public Domain Status Code: {res.status_code}")
except Exception as e:
    print(f"Public domain error: {e}")
