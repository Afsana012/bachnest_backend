"""Test various R2 endpoint candidates."""

import httpx

candidates = [
    "https://b8cd4cd7a066d781bc0a23ccd79b99d7.r2.cloudflarestorage.com",
    "https://7b2b503530b54d9083f1672a82640ade.r2.cloudflarestorage.com",
    "https://r2.cloudflarestorage.com",
]

for c in candidates:
    try:
        res = httpx.get(c, timeout=5.0)
        print(f"[OK] {c} -> {res.status_code}")
    except Exception as e:
        print(f"[FAIL] {c} -> {e}")
