import json
from dotenv import load_dotenv
from pathlib import Path
from os import environ
from fractions import Fraction

def load_config():
    # Load environment variables from .env files
    load_dotenv("Config/.env")
    load_dotenv("API/.env")

    # Load values from config.json
    config_path = Path("Config/bot_config.json")
    if not config_path.exists():
        raise FileNotFoundError("The config.json file is missing. Please create it to configure the bot.")

    with open(file=config_path, mode="r", encoding="utf-8") as config_file:
        config = json.load(config_file)

    # Process ECONOMY_HEALTH_MESSAGES to inject config values and convert types
    economy_messages = config.get("ECONOMY_HEALTH_MESSAGES", [])
    for message in economy_messages:
        message["threshold"] = Fraction(message["threshold"])
        message["message"] = message["message"].replace(
            "{CURRENCY_NAME}",
            config.get("CURRENCY_NAME", "Pint")
        )

    return {
        # Environment variables
        "BOT_TOKEN": environ.get("BOT_TOKEN"),
        "GET_DEBTS_COMMAND": environ.get("GET_DEBTS_COMMAND", "pints"),
        "GET_ALL_DEBTS_COMMAND": environ.get("GET_ALL_DEBTS_COMMAND", "all_pints"),
        "MAXIMUM_PER_DEBT": int(environ.get("MAXIMUM_PER_DEBT", "10")),
        "SMALLEST_UNIT": Fraction(environ.get("SMALLEST_UNIT", "1/6")),
        "MAXIMUM_DEBT_CHARACTER_LIMIT": int(environ.get("MAXIMUM_DEBT_CHARACTER_LIMIT", "200")),
        "QUANTIZE_SETTLING_DEBTS": environ.get("QUANTIZE_SETTLING_DEBTS", "True") == "True",

        # JSON config
        "BOT_NAME": config.get("BOT_NAME", "Pint Bot"),
        "CURRENCY_NAME": config.get("CURRENCY_NAME", "Pint"),
        "CURRENCY_NAME_PLURAL": config.get("CURRENCY_NAME_PLURAL", "Pints"),
        "USE_DECIMAL_OUTPUT": config.get("USE_DECIMAL_OUTPUT", False),
        "USE_TABLE_FORMAT_DEFAULT": config.get("USE_TABLE_FORMAT_DEFAULT", False),
        "SHOW_PERCENTAGES_DEFAULT": config.get("SHOW_PERCENTAGES_DEFAULT", False),
        "PERCENTAGE_DECIMAL_PLACES": config.get("PERCENTAGE_DECIMAL_PLACES", 0),
        "REACT_TO_MESSAGES_MENTIONING_CURRENCY": config.get("REACT_TO_MESSAGES_MENTIONING_CURRENCY", False),
        "REACTION_EMOJI": config.get("REACTION_EMOJI", "🍺"),
        "TRANSFERABLE_ITEMS": config.get("TRANSFERABLE_ITEMS", []),
        "ECONOMY_HEALTH_MESSAGES": economy_messages,
        "API_URL": config.get("API_URL", "http://127.0.0.1:8000"),
    }
