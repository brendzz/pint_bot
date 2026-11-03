"""Shared, platform-agnostic display-name resolution with a TTL cache.

Each adapter supplies an ``async fetch(user_id) -> str | None`` callable
(e.g. Discord's ``client.fetch_user``, Telegram's ``bot.get_chat``).
Failures resolve to ``"Unknown User (<id>)"`` rather than raising — a
missing name must never break a command.
"""
import time
from typing import Awaitable, Callable

_CACHE_TTL_SECONDS = 600          # 10 minutes
_CACHE_MAX_ENTRIES = 1000

# user_id -> (display_name, monotonic timestamp of when it was stored)
_display_name_cache: dict[str, tuple[str, float]] = {}


def _cache_get(user_id: str) -> str | None:
    entry = _display_name_cache.get(user_id)
    if entry is None:
        return None
    name, stored_at = entry
    if time.monotonic() - stored_at >= _CACHE_TTL_SECONDS:
        _display_name_cache.pop(user_id, None)
        return None
    return name


def _cache_set(user_id: str, name: str) -> None:
    while len(_display_name_cache) >= _CACHE_MAX_ENTRIES:
        # Evict the oldest entry (dicts preserve insertion order)
        _display_name_cache.pop(next(iter(_display_name_cache)))
    _display_name_cache[user_id] = (name, time.monotonic())


def clear_display_name_cache() -> None:
    """Drop all cached display names (used in tests and by /refresh_name)."""
    _display_name_cache.clear()


async def resolve_display_name(
    user_id: str,
    fetch: Callable[[str], Awaitable[str | None]],
    *,
    force_refresh: bool = False,
) -> str:
    """Return the display name for ``user_id``, fetching and caching it if needed."""
    user_id = str(user_id)
    if not force_refresh:
        cached = _cache_get(user_id)
        if cached is not None:
            return cached
    try:
        name = await fetch(user_id)
    except Exception:
        name = None
    if not name:
        name = f"Unknown User ({user_id})"
    _cache_set(user_id, name)
    return name
