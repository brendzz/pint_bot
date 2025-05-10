from dotenv import load_dotenv
from os import environ
from fractions import Fraction

# Config for the bot
BOT_NAME: str = "Pint Bot"
CURRENCY_NAME: str = "Pint"
CURRENCY_NAME_PLURAL: str = "Pints"

GET_DEBTS_COMMAND: str = "pints"
GET_ALL_DEBTS_COMMAND: str = "all_pints"

API_URL: str= "http://api:8000"

QUANTIZE_SETTLING_DEBTS:  bool = True
USE_DECIMAL_OUTPUT: bool = False
USE_TABLE_FORMAT_DEFAULT: bool = False
SHOW_PERCENTAGES_DEFAULT: bool = False

PERCENTAGE_DECIMAL_PLACES: int = 1
MAXIMUM_PER_DEBT: int = 10
SMALLEST_UNIT: Fraction = Fraction(1, 6)
MAXIMUM_DEBT_CHARACTER_LIMIT: int = 200

REACT_TO_MESSAGES_MENTIONING_CURRENCY: bool = True
REACTION_EMOJI: str ="🍺"
REACTION_EMOJI_RARE: str ="🍻"
REACTION_ODDS: float = 0.5
REACTION_ODDS_RARE: float = 0.1

TRANSFERABLE_ITEMS = [
    "1 Pint of liquid from a pub",
    "£6 of board games from Thirsty Meeples (preferably ordered via Brendan's account so he can collect the Meeple Points)",
    "3 Scoops of Ice Cream/Gelato from G&Ds in Oxford",
    "Other things if you can convince me"
]

ECONOMY_HEALTH_MESSAGES: list[dict[str, str]] = [
    {"threshold": 20, "message": f"The {CURRENCY_NAME} economy is booming! Prosperity for all!"},
    {"threshold": 15, "message": f"The {CURRENCY_NAME} economy is in great shape!"},
    {"threshold": 10, "message": f"The {CURRENCY_NAME} economy is stable."},
    {"threshold": 5, "message": f"The {CURRENCY_NAME} economy is in terrible shape. Please add debts to avoid imminent financial crash!"},
    {"threshold": 0, "message": f"The {CURRENCY_NAME} economy is in shambles! Financial Crash!"}
]