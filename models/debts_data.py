from typing import Dict
from pydantic import BaseModel
from models.user_debts import UserDebts

class DebtsData(BaseModel):
    """Data structure for managing debts for multiple users."""
    debtors: Dict[str, UserDebts]
