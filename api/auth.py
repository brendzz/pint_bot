"""Optional API-key authentication for the API.

Set the ``API_KEY`` environment variable on the API to require callers
to send a matching ``X-API-Key`` header. When ``API_KEY`` is unset the
API remains open (development default) and a warning is logged on startup.
"""
import hmac
import logging
import os

from fastapi import HTTPException, Security, status
from fastapi.security import APIKeyHeader

logger = logging.getLogger(__name__)

API_KEY_ENV_VAR = "API_KEY"
API_KEY_HEADER = "X-API-Key"

_api_key_header = APIKeyHeader(name=API_KEY_HEADER, auto_error=False)


def get_api_key() -> str | None:
    """Return the configured API key, or None if authentication is disabled."""
    key = os.environ.get(API_KEY_ENV_VAR, "").strip()
    return key or None


if get_api_key() is None:
    logger.warning(
        "%s is not set — the API is unauthenticated. "
        "Set %s to require the %s header.",
        API_KEY_ENV_VAR, API_KEY_ENV_VAR, API_KEY_HEADER,
    )


async def require_api_key(api_key: str | None = Security(_api_key_header)) -> None:
    """FastAPI dependency that enforces the API key when one is configured."""
    expected = get_api_key()
    if expected is None:
        return  # Auth disabled; open access.
    if api_key is None or not hmac.compare_digest(api_key, expected):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="INVALID_API_KEY",
        )
