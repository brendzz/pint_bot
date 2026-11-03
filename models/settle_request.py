from pydantic import BaseModel, Field

from models.limits import MAXIMUM_DEBT_CHARACTER_LIMIT

class SettleRequest(BaseModel):
    """Represents a request to settle a debt between two users."""
    debtor: int = Field(gt=0)
    creditor: int = Field(gt=0)
    amount: str
    reason: str = Field(default="", max_length=MAXIMUM_DEBT_CHARACTER_LIMIT)
