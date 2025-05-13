from pydantic import BaseModel, Field
from typing import List, Dict

from models.debt_entry import DebtEntry

class UserDebts(BaseModel):
    """Represents the debts of a user."""
    creditors: Dict[str, List[DebtEntry]] = Field(default_factory=dict)
