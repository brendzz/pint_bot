import sys
import os
from unittest.mock import patch
import pytest
from fractions import Fraction

# Add the project root to the import path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Add the bot folder to the import path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'bot')))

PATCHED_CONFIG = {
    "CURRENCY_NAME": "TestCoin",
    "CURRENCY_NAME_PLURAL": "TestCoins",
    "BOT_NAME": "TestBot",
    "GET_DEBTS_COMMAND": "testcoins",
    "GET_ALL_DEBTS_COMMAND": "all_testcoins",
    "DEBTS_WITH_USER_COMMAND": "testcoins_with_user",
    "TRANSFERABLE_ITEMS": ["Beer", "Wine"],
    "SHOW_PERCENTAGES_DEFAULT": False,
    "USE_TABLE_FORMAT_DEFAULT": True,
    "ECONOMY_HEALTH_MESSAGES": [
        {"threshold": 0, "message": "Economy is dead"},
        {"threshold": 1, "message": "Economy active"},
    ],
    "MAXIMUM_PER_DEBT": 10,
    "SMALLEST_UNIT": Fraction(1, 6),
    "MAXIMUM_DEBT_CHARACTER_LIMIT": 200,
    "QUANTIZE_SETTLING_DEBTS": True,
    "SHOW_DETAILS_DEFAULT": True,
}

@pytest.fixture(autouse=True, scope="session")
def patch_config_before_tests():
    with patch.multiple("bot.utilities.error_handling.config", **PATCHED_CONFIG), \
         patch.multiple("bot.utilities.formatter.config", **PATCHED_CONFIG), \
         patch.multiple("bot.bot_commands.config", **PATCHED_CONFIG):
        yield