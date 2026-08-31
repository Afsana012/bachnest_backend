"""Network target helpers for safe diagnostics logging."""

from urllib.parse import urlsplit

_DEFAULT_PORTS = {
    "postgres": 5432,
    "postgresql": 5432,
    "redis": 6379,
    "rediss": 6379,
}


def masked_target(url: str) -> str:
    """Return host:port/dbname of a service URL with credentials stripped."""
    try:
        parts = urlsplit(url)
        scheme = parts.scheme.lower()
        host = parts.hostname or "unknown"
        port = parts.port or _DEFAULT_PORTS.get(scheme, 0)
        path = parts.path.lstrip("/") or "-"
        return f"{host}:{port}/{path}"
    except Exception:
        return "unknown"
