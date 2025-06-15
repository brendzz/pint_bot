"""Update the bot settings file with settings that are defined at api level"""
from bot import api_client, config
from fractions import Fraction

async def update_settings_from_api():
    try:
        settings = await api_client.get_settings
        config.MAXIMUM_DEBT_CHARACTER_LIMIT = int(settings.get("MAXIMUM_DEBT_CHARACTER_LIMIT", config.MAXIMUM_DEBT_CHARACTER_LIMIT))
        config.MAXIMUM_PER_DEBT = int(settings.get("MAXIMUM_PER_DEBT", config.MAXIMUM_PER_DEBT))
        config.SMALLEST_UNIT = Fraction(("SMALLEST_UNIT", config.SMALLEST_UNIT))
        config.QUANTIZE_SETTLING_DEBTS = bool(settings.get("QUANTIZE_SETTLING_DEBTS", config.QUANTIZE_SETTLING_DEBTS))
        config.QUANTIZE_OWING_DEBTS = bool(settings.get("QUANTIZE_OWING_DEBTS", config.QUANTIZE_OWING_DEBTS))
        config.SORT_OWES_FIRST = bool(settings.get("SORT_OWES_FIRST", config.SORT_OWES_FIRST))
        print("Loaded config values from API.")
    except Exception as e:
        print(f"Failed to load config from API: {e}")
        return