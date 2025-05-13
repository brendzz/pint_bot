from pydantic import BaseModel, Field
import os

MAXIMUM_DEBT_CHARACTER_LIMIT = int(os.environ.get("MAXIMUM_DEBT_CHARACTER_LIMIT", "200")) 

class OweRequest(BaseModel):
    """Represents a request to add a debt between two users."""
    debtor: int
    creditor: int
    amount: str
    reason: str = Field(default="", max_length=MAXIMUM_DEBT_CHARACTER_LIMIT)  # Optional field with a max length of 200 characters
