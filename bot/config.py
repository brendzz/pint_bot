"""Configuration for the bot."""
from fractions import Fraction
from secrets import SystemRandom

RANDOM_NUMBER_GENERATOR = SystemRandom()

# Config for the bot
BOT_NAME: str = "Pint Bot"
CURRENCY_NAME: str = "Pint"
CURRENCY_NAME_PLURAL: str = "Pints"

GET_DEBTS_COMMAND: str = "pints"
GET_ALL_DEBTS_COMMAND: str = "all_pints"
DEBTS_WITH_USER_COMMAND: str = "pints_with_user"
ROLL_COMMAND: str = "volcano"

API_URL: str= "http://localhost:8000"

QUANTIZE_SETTLING_DEBTS:  bool = True
USE_DECIMAL_OUTPUT: bool = False
USE_TABLE_FORMAT_DEFAULT: bool = False
SHOW_PERCENTAGES_DEFAULT: bool = False
PERCENTAGE_DECIMAL_PLACES: int = 1

SHOW_DETAILS_DEFAULT: bool = False

MAXIMUM_PER_DEBT: int = 10
SMALLEST_UNIT: Fraction = Fraction(1, 6)
MAXIMUM_DEBT_CHARACTER_LIMIT: int = 200

REACT_TO_MESSAGES_MENTIONING_CURRENCY: bool = True
REACTION_EMOJI: str ="🍺"
REACTION_EMOJI_RARE: str ="🍻"
REACTION_ODDS: float = 0.5
REACTION_ODDS_RARE: float = 0.1

ROLL_WINNING_NUMBER: int = 6

TRANSFERABLE_ITEMS = [
    "1 Pint of liquid from a pub",
    "£6 of board games from Thirsty Meeples (preferably ordered via Brendan's account so he can collect the Meeple Points)",
    "3 Scoops of Ice Cream/Gelato from G&Ds in Oxford",
    "Other things if you can convince me"
]

ECONOMY_HEALTH_MESSAGES: list[dict[str, Fraction | str]] = [
    {
        "threshold": Fraction(100),
        "message": 
            f"{CURRENCY_NAME} Level 100/10 - "
            f"The levels of {CURRENCY_NAME_PLURAL} is off the scale! We have broken reality!"
    },
    {
        "threshold": Fraction(75),
        "message": 
            f"{CURRENCY_NAME} Level 11/10 - "
            f"We are going beyond into infinite {CURRENCY_NAME} realm!"
    },
    {
        "threshold": Fraction(50),
        "message": 
            f"{CURRENCY_NAME} Level 10/10 - "
            f"We have reached peak {CURRENCY_NAME_PLURAL}! "
            f"{BOT_NAME} has now achieved sentience! All hail {BOT_NAME}!"
    },
    {
        "threshold": Fraction(45),
        "message": 
            f"{CURRENCY_NAME} Level 9/10 - "
            f"The {CURRENCY_NAME} economy is in a golden era! "
            f"The people are thriving and the {CURRENCY_NAME_PLURAL} are flowing!"
    },
    {
        "threshold": Fraction(40),
        "message":
            f"{CURRENCY_NAME} Level 8/10 - "
            f"The {CURRENCY_NAME} economy is booming! Prosperity for all!"
    },
    {
        "threshold": Fraction(35),
        "message": 
            f"{CURRENCY_NAME} Level 7/10 - "
            f"The {CURRENCY_NAME} economy is in great shape!"
    },
    {
        "threshold": Fraction(30),
        "message": 
            f"{CURRENCY_NAME} Level 6/10 - "
            f"The {CURRENCY_NAME} economy is looking pretty nice."
    },
    {
        "threshold": Fraction(25),
        "message": 
            f"{CURRENCY_NAME} Level 5/10 - "
            f"The {CURRENCY_NAME} economy is stable."
    },
    {
        "threshold": Fraction(20),
        "message": 
            f"{CURRENCY_NAME} Level 4/10 - "
            f"The {CURRENCY_NAME} economy is approaching stability."
    },
    {
        "threshold": Fraction(15),
        "message": 
            f"{CURRENCY_NAME} Level 3/10 - "
            f"The {CURRENCY_NAME} economy is underwhelming. Do better."
    },
    {
        "threshold": Fraction(10),
        "message": 
            f"{CURRENCY_NAME} Level 2/10 - "
            f"The {CURRENCY_NAME} economy has seen better days."
    },
    {
        "threshold": Fraction(5),
        "message": 
            f"{CURRENCY_NAME} Level 1/10 - "
            f"The {CURRENCY_NAME} economy is in terrible shape. "
            f"Please add debts to avoid imminent financial crash!"
    },
    {
        "threshold": Fraction(0),
        "message": 
            f"{CURRENCY_NAME} Level 0/10 - "
            f"The {CURRENCY_NAME} economy is in shambles! Financial Crash!"
    }
]
