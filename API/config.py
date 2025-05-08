import json
from dotenv import load_dotenv
from pathlib import Path
from os import environ
from fractions import Fraction

def load_config():
    # Load environment variables from .env file
    load_dotenv("api/.env")

    return {
        # Environment variables
        "DATA_FILE": environ.get("DATA_FILE", "PintEconomy.json"),
        "SMALLEST_UNIT": Fraction(environ.get("SMALLEST_UNIT", "1/6")),
        "QUANTIZE_SETTLING_DEBTS": environ.get("QUANTIZE_SETTLING_DEBTS", "True") == "True",
        "GET_DEBTS_COMMAND": environ.get("GET_DEBTS_COMMAND", "pints"),
        "GET_ALL_DEBTS_COMMAND": environ.get("GET_ALL_DEBTS_COMMAND", "all_pints"),
        "MAXIMUM_PER_DEBT": int(environ.get("MAXIMUM_PER_DEBT", "10")),
        "MAXIMUM_DEBT_CHARACTER_LIMIT": int(environ.get("MAXIMUM_DEBT_CHARACTER_LIMIT", "200")),
    }