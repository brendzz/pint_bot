"""Module for interacting with the API.

All functions are async; the blocking ``requests`` calls are run in a
worker thread via :func:`asyncio.to_thread` so the Discord event loop
is never blocked. When the ``API_KEY`` environment variable (or the
``API_KEY`` setting in ``bot/config.py``) is set, it is sent as the
``X-API-Key`` header on every request.
"""
import asyncio
import requests
import bot.config as config
from typing import Optional, Any, Dict


def _headers() -> dict:
    if config.API_KEY:
        return {"X-API-Key": config.API_KEY}
    return {}


def _request(method: str, path: str, **kwargs) -> requests.Response:
    response = requests.request(
        method,
        f"{config.API_URL}{path}",
        headers=_headers(),
        timeout=config.API_TIMEOUT,
        **kwargs,
    )
    response.raise_for_status()
    return response


async def add_debt(payload: dict):
    """Add a debt for a user in the API."""
    response = await asyncio.to_thread(_request, "POST", "/debts", json=payload)
    return response.json()


async def get_debts(user_id: str):
    """Get the debts for a specific user from the API."""
    response = await asyncio.to_thread(_request, "GET", f"/users/{user_id}/debts")
    return response.json()


async def get_all_debts():
    """Get all debts from the API."""
    response = await asyncio.to_thread(_request, "GET", "/debts")
    return response.json()


async def debts_with_user(user_id1: str, user_id2: str):
    """Get all debts between two users from the API."""
    response = await asyncio.to_thread(
        _request, "GET", "/debts/between",
        params={"requester_id": user_id1, "target_id": user_id2},
    )
    return response.json()


async def settle_debt(payload: dict):
    """Settle a user's debt in the API."""
    response = await asyncio.to_thread(_request, "PATCH", "/debts", json=payload)
    return response.json()


async def get_unicode_preference(user_id: str):
    """Get the user's Unicode preference from the API."""
    response = await asyncio.to_thread(_request, "GET", f"/users/{user_id}/unicode_preference")
    return response.json()


async def set_unicode_preference(user_id: str, payload: dict):
    """Set the user's Unicode preference in the API."""
    response = await asyncio.to_thread(_request, "POST", f"/users/{user_id}/unicode_preference", json=payload)
    return response.json()


async def get_settings():
    """Get the configuration values which have been set in the API."""
    response = await asyncio.to_thread(_request, "GET", "/settings")
    return response.json()


async def get_transactions(
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        user_id: Optional[str] = None,
        transaction_type: Optional[str] = None,
) -> Dict[str, Any]:
    params = {}
    if start_date:
        params["start_date"] = start_date
    if end_date:
        params["end_date"] = end_date
    if user_id:
        params["user_id"] = user_id
    if transaction_type:
        params["type"] = transaction_type
    response = await asyncio.to_thread(_request, "GET", "/transactions", params=params)
    return response.json()
