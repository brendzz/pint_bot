import json
from dotenv import load_dotenv
from pathlib import Path
from os import environ
from fractions import Fraction

# The name of the file where the economy data is stored
# This file should be in the same directory as the script
DATA_FILE: str = "PintEconomy.json"

# Set the name for the command used to get the debts of a user
GET_DEBTS_COMMAND: str = "pints" 

# Set the name for the command used to get the debts of ALL users
GET_ALL_DEBTS_COMMAND: str = "all_pints"

# Set the maximum amount of currency allowed in each individual debt
# No single debt can be more than this amount
# Users can still owe more than this, but will need to split it into multiple debts
MAXIMUM_PER_DEBT: int = 10

# The API internally converts everything to Fractions so it can deal with fractional debts.
# Set this to the allowed smallest fraction of the currency that can be used in the economy
# If you would like to use whole numbers only, set this to 1
SMALLEST_UNIT: Fraction = 1/6

#Set the maximum character limit for the debt descriptions
MAXIMUM_DEBT_CHARACTER_LIMIT: int = 200

# Set to True to only allow Settling debts in quantities of the smallest unit
QUANTIZE_SETTLING_DEBTS: bool = True