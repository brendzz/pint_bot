from pydantic import BaseModel

class DebtsWithUser(BaseModel):
    """Represents a request to view debts between two users."""
    user_id: str
    other_user_id: str
