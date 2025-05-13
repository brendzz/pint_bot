from pydantic import BaseModel

class SettleRequest(BaseModel):
    """Represents a request to settle a debt between two users."""
    debtor: int
    creditor: int
    amount: str
