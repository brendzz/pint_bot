from pydantic import BaseModel, Field
from fractions import Fraction
import os

MAXIMUM_DEBT_CHARACTER_LIMIT = int(os.environ.get("MAXIMUM_DEBT_CHARACTER_LIMIT", "200"))

class DebtEntry(BaseModel):
    """Represents a debt entry between two users."""
    amount: Fraction = Field(gt=0, le=10)
    reason: str = Field(default="",max_length=MAXIMUM_DEBT_CHARACTER_LIMIT)
    timestamp: str
