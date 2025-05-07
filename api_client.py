import requests

from bot_config import get_config

def get_api_url():
    return get_config()["API_URL"]

def add_debt(payload: dict):
    response = requests.post(f"{get_api_url()}/owe", json=payload)
    response.raise_for_status()
    return response.json()

def get_debts(user_id: int):
    response = requests.get(f"{get_api_url()}/{get_config()["GET_DEBTS_COMMAND"]}/{user_id}")
    response.raise_for_status()
    return response.json()

def get_all_debts():
    response = requests.get(f"{get_api_url()}/{get_config()["GET_ALL_DEBTS_COMMAND"]}")
    response.raise_for_status()
    return response.json()

def settle_debt(payload: dict):
    response = requests.post(f"{get_api_url()}/settle", json=payload)
    response.raise_for_status()
    return response.json()

def get_unicode_preference(user_id: int):
    response = requests.get(f"{get_api_url()}/get_unicode_preference/{user_id}")
    response.raise_for_status()
    return response.json()

def set_unicode_preference(payload: dict):
    response = requests.post(f"{get_api_url()}/set_unicode_preference", json=payload)
    response.raise_for_status()
    return response.json()