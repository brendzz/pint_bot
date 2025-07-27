"""Module for interacting with the API."""
import requests
import bot.config as config
from typing import Optional, Any, Dict

def add_debt(payload: dict):
    """Add a debt for a user in the API."""
    response = requests.post(f"{config.API_URL}/debts", json=payload, timeout=config.API_TIMEOUT)
    response.raise_for_status()
    return response.json()

def get_debts(user_id: str):
    """Get the debts for a specific user from the API."""
    response = requests.get(f"{config.API_URL}/users/{user_id}/debts", timeout=config.API_TIMEOUT)
    response.raise_for_status()
    return response.json()

def get_all_debts():
    """Get all debts from the API."""
    response = requests.get(f"{config.API_URL}/debts", timeout=config.API_TIMEOUT)
    response.raise_for_status()
    return response.json()

def debts_with_user(user_id1: str, user_id2: str):
    """Get all debts between two users from the API."""
    response = requests.get(f"{config.API_URL}/debts/between", params={"requester_id": user_id1, "target_id": user_id2}, timeout=config.API_TIMEOUT)
    response.raise_for_status()
    return response.json()

def settle_debt(payload: dict):
    """Settle a user's debt in the API."""
    response = requests.patch(f"{config.API_URL}/debts", json=payload, timeout=config.API_TIMEOUT)
    response.raise_for_status()
    return response.json()

def get_unicode_preference(user_id: str):
    """Get the user's Unicode preference from the API."""
    response = requests.get(f"{config.API_URL}/users/{user_id}/unicode_preference", timeout=config.API_TIMEOUT)
    response.raise_for_status()
    return response.json()

def set_unicode_preference(user_id: str, payload: dict):
    """Set the user's Unicode preference in the API."""
    response = requests.post(f"{config.API_URL}/users/{user_id}/unicode_preference", json=payload, timeout=config.API_TIMEOUT)
    response.raise_for_status()
    return response.json()

def get_settings():
    """Get the configuration values which have been set in the API."""
    response = requests.get(f"{config.API_URL}/settings", timeout=config.API_TIMEOUT)
    response.raise_for_status()
    return response.json()

def get_transactions(
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        user_id: Optional[int] = None,
        transaction_type: Optional[str] = None
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
    response = requests.get(f"{config.API_URL}/transactions", params=params, timeout=config.API_TIMEOUT)
    response.raise_for_status()
    return response.json()
