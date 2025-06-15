"""Configuration for the API."""
from fractions import Fraction
from pathlib import Path

# The name of the file where the economy data is stored
# This file should be in the same directory as the script
BASE = Path(__file__).parent
DATA_FILE = BASE / "pint_economy.json"

# Set the maximum amount of currency allowed in each individual debt
# No single debt can be more than this amount
# Users can still owe more than this, but will need to split it into multiple debts
MAXIMUM_PER_DEBT: int = 10

# The API internally converts everything to Fractions so it can deal with fractional debts.
# Set this to the allowed smallest fraction of the currency that can be used in the economy
# If you would like to use whole numbers only, set this to 1
SMALLEST_UNIT: Fraction = Fraction(1, 6)

#Set the maximum character limit for the debt descriptions
MAXIMUM_DEBT_CHARACTER_LIMIT: int = 200

# Set to True to only allow Settling debts in quantities of the smallest unit
QUANTIZE_SETTLING_DEBTS: bool = True
QUANTIZE_OWING_DEBTS: bool = True

# True = sort debts most owed by user to least owed, false = sort by most owed to user to least
SORT_OWES_FIRST: bool = True