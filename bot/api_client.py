"""Module for interacting with the API."""
import requests
import bot.config as config

def add_debt(payload: dict):
    """Add a debt for a user in the API."""
    response = requests.post(f"{config.API_URL}/debts", json=payload)
    response.raise_for_status()
    return response.json()

def get_debts(user_id: str):
    """Get the debts for a specific user from the API."""
    response = requests.get(f"{config.API_URL}/users/{user_id}/debts")
    response.raise_for_status()
    return response.json()

def get_all_debts():
    """Get all debts from the API."""
    response = requests.get(f"{config.API_URL}/debts")
    response.raise_for_status()
    return response.json()

def debts_with_user(user_id1: str, user_id2: str):
    """Get all debts between two users from the API."""
    response = requests.get(f"{config.API_URL}/debts/between", params={"requester_id": user_id1, "target_id": user_id2})
    response.raise_for_status()
    return response.json()

def settle_debt(payload: dict):
    """Settle a user's debt in the API."""
    response = requests.patch(f"{config.API_URL}/debts", json=payload)
    response.raise_for_status()
    return response.json()

def get_unicode_preference(user_id: str):
    """Get the user's Unicode preference from the API."""
    response = requests.get(f"{config.API_URL}/users/{user_id}/unicode_preference")
    response.raise_for_status()
    return response.json()

def set_unicode_preference(user_id: str, payload: dict):
    """Set the user's Unicode preference in the API."""
    response = requests.post(f"{config.API_URL}/users/{user_id}/unicode_preference", json=payload)
    response.raise_for_status()
    return response.json()

def get_settings():
    """Set the user's Unicode preference in the API."""
    response = requests.get(f"{config.API_URL}/settings")
    response.raise_for_status()
    return response.json()