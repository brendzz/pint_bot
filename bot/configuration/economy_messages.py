"""Configuration for the bot."""
from fractions import Fraction
from bot.configuration.constants import BOT_NAME, CURRENCY_NAME, CURRENCY_NAME_PLURAL
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

SECRET_ECONOMY_MESSAGES = {
    Fraction(3.14): f"Pi time",
    Fraction(13): f"A spooky number of {CURRENCY_NAME_PLURAL} indeed.",
    Fraction(42): f"The answer to life, the universe, and everything is {CURRENCY_NAME_PLURAL}!",
    Fraction(69): "Nice.",
    Fraction(100): "Pints are now exactly equal to percentage! 1 pint = 1%!",
}