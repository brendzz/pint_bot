from pydantic import BaseModel, Field
from fractions import Fraction

from models.limits import MAXIMUM_DEBT_CHARACTER_LIMIT

class DebtEntry(BaseModel):
    """Represents a debt entry between two users."""
    # The upper bound is enforced at the API layer (see MAXIMUM_PER_DEBT in
    # api/config.py); the model only guarantees the amount is positive.
    amount: Fraction = Field(gt=0)
    reason: str = Field(default="", max_length=MAXIMUM_DEBT_CHARACTER_LIMIT)
    timestamp: str
