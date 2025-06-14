"""Configuration for the bot."""
from secrets import SystemRandom
import os
from fractions import Fraction
from bot.configuration.economy_health_messages import ECONOMY_HEALTH_MESSAGES, SECRET_ECONOMY_MESSAGES
from bot.configuration.transferable_items import TRANSFERABLE_ITEMS
from bot.configuration.constants import BOT_NAME, CURRENCY_NAME, CURRENCY_NAME_PLURAL
# API Connection
API_URL: str = os.getenv("API_URL", "http://api:8000")

# Misc
RANDOM_NUMBER_GENERATOR = SystemRandom()

# General
BOT_NAME=BOT_NAME
CURRENCY_NAME=CURRENCY_NAME
CURRENCY_NAME_PLURAL=CURRENCY_NAME_PLURAL

# Commands
GET_DEBTS_COMMAND: str = "pints"
GET_ALL_DEBTS_COMMAND: str = "all_pints"
DEBTS_WITH_USER_COMMAND: str = "pints_with_user"
ROLL_COMMAND: str = "volcano"

# Display
USE_DECIMAL_OUTPUT: bool = False
USE_TABLE_FORMAT_DEFAULT: bool = False
SHOW_PERCENTAGES_DEFAULT: bool = False
PERCENTAGE_DECIMAL_PLACES: int = 1
SHOW_DETAILS_DEFAULT: bool = False
SORT_OWES_FIRST: bool = True

# API Debt Rules
QUANTIZE_SETTLING_DEBTS:  bool = True
QUANTIZE_OWING_DEBTS:  bool = True
MAXIMUM_PER_DEBT: int = 10
SMALLEST_UNIT: Fraction = Fraction(1, 6)
MAXIMUM_DEBT_CHARACTER_LIMIT: int = 200

# Reactions
REACT_TO_MESSAGES_MENTIONING_CURRENCY: bool = True
REACTION_EMOJI: str ="🍺"
REACTION_EMOJI_RARE: str ="🍻"
REACTION_ODDS: float = 0.5
REACTION_ODDS_RARE: float = 0.1

# Fun
ROLL_WINNING_NUMBER: int = 6

ECONOMY_HEALTH_MESSAGES=ECONOMY_HEALTH_MESSAGES
SECRET_ECONOMY_MESSAGES=SECRET_ECONOMY_MESSAGES
TRANSFERABLE_ITEMS=TRANSFERABLE_ITEMS
