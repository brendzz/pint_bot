import requests
import json
from pathlib import Path
from config import load_config

CONFIG = load_config()
GET_DEBTS_COMMAND = CONFIG["GET_DEBTS_COMMAND"]
GET_ALL_DEBTS_COMMAND = CONFIG["GET_ALL_DEBTS_COMMAND"]

config_path = Path("Config/bot_config.json")
if not config_path.exists():
    raise FileNotFoundError("The config.json file is missing. Please create it to configure the bot.")

with open(config_path, "r") as config_file:
    config = json.load(config_file)
API_URL = config.get("API_URL", "http://127.0.0.1:8000")

def add_debt(payload: dict):
    response = requests.post(f"{API_URL}/owe", json=payload)
    response.raise_for_status()
    return response.json()

def get_debts(user_id: int):
    response = requests.get(f"{API_URL}/{GET_DEBTS_COMMAND}/{user_id}")
    response.raise_for_status()
    return response.json()

def get_all_debts():
    response = requests.get(f"{API_URL}/{GET_ALL_DEBTS_COMMAND}")
    response.raise_for_status()
    return response.json()

def settle_debt(payload: dict):
    response = requests.post(f"{API_URL}/settle", json=payload)
    response.raise_for_status()
    return response.json()

def get_unicode_preference(user_id: int):
    response = requests.get(f"{API_URL}/get_unicode_preference/{user_id}")
    response.raise_for_status()
    return response.json()

def set_unicode_preference(payload: dict):
    response = requests.post(f"{API_URL}/set_unicode_preference", json=payload)
    response.raise_for_status()
    return response.json()