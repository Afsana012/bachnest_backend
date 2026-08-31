"""Probe which database/redis addresses are reachable from inside this container.

Usage: python scripts/db_probe.py
"""

import os
import socket
import sys
from urllib.parse import urlsplit

TIMEOUT_SECONDS = 3

POSTGRES_CANDIDATES = [
    ("169.58.200.32", 5433),
    ("host.docker.internal", 5433),
    ("host.docker.internal", 5432),
    ("172.17.0.1", 5433),
    ("172.17.0.1", 5432),
    ("postgres", 5432),
    ("localhost", 5433),
    ("localhost", 5432),
]

REDIS_CANDIDATES = [
    ("169.58.200.32", 6380),
    ("host.docker.internal", 6380),
    ("host.docker.internal", 6379),
    ("172.17.0.1", 6380),
    ("172.17.0.1", 6379),
    ("redis", 6379),
    ("localhost", 6380),
    ("localhost", 6379),
]


def probe(host: str, port: int) -> bool:
    try:
        with socket.create_connection((host, port), timeout=TIMEOUT_SECONDS):
            return True
    except Exception:
        return False


def describe(url: str) -> str:
    try:
        parts = urlsplit(url)
        return f"{parts.hostname}:{parts.port}"
    except Exception:
        return "?"


def main() -> int:
    db_url = os.environ.get("DATABASE_URL", "(not set)")
    redis_url = os.environ.get("REDIS_URL", "(not set)")

    print("Currently configured targets")
    print(f"  DATABASE_URL -> {db_url if db_url == '(not set)' else describe(db_url)}")
    print(f"  REDIS_URL    -> {redis_url if redis_url == '(not set)' else describe(redis_url)}")

    print("\nPostgreSQL reachability")
    db_ok = []
    for host, port in POSTGRES_CANDIDATES:
        reachable = probe(host, port)
        if reachable:
            db_ok.append((host, port))
        print(f"  {host}:{port:<5} {'REACHABLE' if reachable else 'no'}")

    print("\nRedis reachability")
    redis_ok = []
    for host, port in REDIS_CANDIDATES:
        reachable = probe(host, port)
        if reachable:
            redis_ok.append((host, port))
        print(f"  {host}:{port:<5} {'REACHABLE' if reachable else 'no'}")

    print("\nSuggested env values")
    if db_ok:
        host, port = db_ok[0]
        print(f"  DATABASE_URL=postgresql+asyncpg://postgres:<PASSWORD>@{host}:{port}/bachnest")
    else:
        print("  no reachable postgres found from this container")
    if redis_ok:
        host, port = redis_ok[0]
        print(f"  REDIS_URL=redis://default:<PASSWORD>@{host}:{port}/0")
    else:
        print("  no reachable redis found from this container")

    return 0


if __name__ == "__main__":
    sys.exit(main())
