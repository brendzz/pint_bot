"""Configuration for the API."""
from fractions import Fraction

from models.limits import MAXIMUM_DEBT_CHARACTER_LIMIT

# Set the maximum amount of currency allowed in each individual debt
# No single debt can be more than this amount
# Users can still owe more than this, but will need to split it into multiple debts
MAXIMUM_PER_DEBT: int = 10

# The API internally converts everything to Fractions so it can deal with fractional debts.
# Set this to the allowed smallest fraction of the currency that can be used in the economy
# If you would like to use whole numbers only, set this to 1
SMALLEST_UNIT: Fraction = Fraction(1, 6)

#Set the maximum character limit for the debt descriptions
# (shared with the models; override with the MAXIMUM_DEBT_CHARACTER_LIMIT env var)

# Set to True to only allow Settling debts in quantities of the smallest unit
QUANTIZE_SETTLING_DEBTS: bool = True
QUANTIZE_OWING_DEBTS: bool = True

# True = sort debts most owed by user to least owed, false = sort by most owed to user to least
SORT_OWES_FIRST: bool = True

# Set to True to allow a settle/cashout larger than the debt it settles.
# When enabled, the excess is NOT discarded: a debt in the opposite direction
# is created automatically. Example: Alice owes Bob 1 pint, Bob cashes out 2
# pints -> Alice's debt is settled, and Bob now owes Alice 1 pint.
# When False (default), the excess is silently dropped (settles what it can).
AUTO_REVERSE_EXCESS_CASHOUTS: bool = False

TRANSACTIONS_DEFAULT_TIME_PERIOD: int = 30
VALID_TRANSACTION_TYPES: set[str] = {"owe", "settle", "cashout"}