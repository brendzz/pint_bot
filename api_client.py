import requests

from bot_config import get_config

def get_api_url():
    """Get the API URL from the configuration."""
    return get_config()["API_URL"]

def add_debt(payload: dict):
    """Add a debt for a user in the API."""
    response = requests.post(f"{get_api_url()}/owe", json=payload)
    response.raise_for_status()
    return response.json()

def get_debts(user_id: str):
    """Get the debts for a specific user from the API."""
    response = requests.get(f"{get_api_url()}/{get_config()["GET_DEBTS_COMMAND"]}/{user_id}")
    response.raise_for_status()
    return response.json()

def get_all_debts():
    """Get all debts from the API."""
    response = requests.get(f"{get_api_url()}/{get_config()["GET_ALL_DEBTS_COMMAND"]}")
    response.raise_for_status()
    return response.json()

def settle_debt(payload: dict):
    """Settle a user's debt in the API."""
    response = requests.post(f"{get_api_url()}/settle", json=payload)
    response.raise_for_status()
    return response.json()

def get_unicode_preference(user_id: str):
    """Get the user's Unicode preference from the API."""
    response = requests.get(f"{get_api_url()}/get_unicode_preference/{user_id}")
    response.raise_for_status()
    return response.json()

def set_unicode_preference(payload: dict):
    """Set the user's Unicode preference in the API."""
    response = requests.post(f"{get_api_url()}/set_unicode_preference", json=payload)
    response.raise_for_status()
    return response.json()