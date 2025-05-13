from pydantic import BaseModel, Field
from typing import List, Dict

from models.debt_entry import DebtEntry

class UserDebts(BaseModel):
    creditors: Dict[str, List[DebtEntry]] = Field(default_factory=dict)
