import requests
from os import environ
from dotenv import load_dotenv
load_dotenv(".env")
API_URL = environ.get("API_URL")

load_dotenv("API/.env")
GET_DEBTS_COMMAND = environ.get("GET_DEBTS_COMMAND")
GET_ALL_DEBTS_COMMAND = environ.get("GET_ALL_DEBTS_COMMAND")


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

def set_preference(user_id: int, use_unicode: bool):
    payload = {"user_id": user_id, "use_unicode": use_unicode}
    response = requests.post(f"{API_URL}/set_preference", json=payload)
    response.raise_for_status()
    return response.json()