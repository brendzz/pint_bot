"""Configuration for the bot."""
from secrets import SystemRandom
import os
from fractions import Fraction
import bot.configuration.economy_messages as economy_messages
import bot.configuration.transferable_items as transferable_items
import bot.configuration.constants as constants

# API Connection
API_URL: str = os.getenv("API_URL", "http://api:8000")
API_TIMEOUT: int = 10

# Discord Constants
DISCORD_EMBED_TITLE_LIMIT = 256
DISCORD_EMBED_DESCRIPTION_LIMIT = 4096

# Misc
RANDOM_NUMBER_GENERATOR = SystemRandom()

# General
BOT_NAME = constants.BOT_NAME
CURRENCY_NAME = constants.CURRENCY_NAME
CURRENCY_NAME_PLURAL = constants.CURRENCY_NAME_PLURAL

# Commands
GET_DEBTS_COMMAND: str = "pints"
GET_ALL_DEBTS_COMMAND: str = "all_pints"
DEBTS_WITH_USER_COMMAND: str = "pints_with_user"
ROLL_COMMAND: str = "volcano"

# Command Categories
DEBT_DISPLAY_COMMAND_CATEGORY: str = "Debt Display"
DEBT_TRANSACTIONS_COMMAND_CATEGORY: str = "Debt Transactions"
SUPPORT_COMMAND_CATEGORY: str = "Support"
SETTINGS_COMMAND_CATEGORY: str = "Settings"
GAMES_COMMAND_CATEGORY: str = "Games"

# Display
USE_DECIMAL_OUTPUT: bool = False
USE_TABLE_FORMAT_DEFAULT: bool = False
SHOW_PERCENTAGES_DEFAULT: bool = False
PERCENTAGE_DECIMAL_PLACES: int = 1
SHOW_DETAILS_DEFAULT: bool = False
SORT_OWES_FIRST: bool = True
SHOW_EMOJI_VISUALS_DEFAULT: bool = False
SHOW_EMOJI_VISUALS_ON_DETAILS_DEFAULT: bool = True
CURRENCY_DISPLAY_EMOJI: str = "🍺"
DATE_FORMAT: str = "%d-%m-%Y" #add %A for day of the week
TIME_FORMAT: str = "%H:%M" #24 hour time, use "%I:%M %p" instead for 12 hour time"
DISPLAY_TRANSACTIONS_AS_SETTLE_DEFAULT: bool = False #if false, will display as 'cashout' instead

# Display - Conversion Currency
CONVERSION_CURRENCY: str = "£"
SHOW_CONVERSION_CURRENCY_DEFAULT: bool = False
EXCHANGE_RATE_TO_CONVERSION_CURRENCY: int = 6
CONVERSION_CURRENCY_SHOW_SYMBOL_BEFORE_AMOUNT: bool = True

# API Debt Rules
QUANTIZE_SETTLING_DEBTS:  bool = True
QUANTIZE_OWING_DEBTS:  bool = True
MAXIMUM_PER_DEBT: int = 10
SMALLEST_UNIT: Fraction = Fraction(1, 6)
MAXIMUM_DEBT_CHARACTER_LIMIT: int = 200
TRANSACTIONS_DEFAULT_TIME_PERIOD: int = 30

# Reactions
REACT_TO_MESSAGES_MENTIONING_CURRENCY: bool = True
REACTION_EMOJI: str = "🍺"
REACTION_EMOJI_RARE: str = "🍻"
REACTION_ODDS: float = 0.5
REACTION_ODDS_RARE: float = 0.1

# Fun
ROLL_WINNING_NUMBER: int = 6

ECONOMY_HEALTH_MESSAGES = economy_messages.ECONOMY_HEALTH_MESSAGES
SECRET_ECONOMY_MESSAGES = economy_messages.SECRET_ECONOMY_MESSAGES
TRANSFERABLE_ITEMS = transferable_items.TRANSFERABLE_ITEMS
