from pydantic import BaseModel, Field
from typing import List, Dict
from fractions import Fraction

class DebtEntry(BaseModel):
    amount: Fraction = Field(gt=0, le=10)
    reason: str = Field(default="",max_length=200)
    timestamp: str

class UserDebts(BaseModel):
    creditors: Dict[str, List[DebtEntry]] = Field(default_factory=dict)

class UserPreferences(BaseModel):
    use_unicode: bool = False

class UserData(BaseModel):
    debts: UserDebts = Field(default_factory=UserDebts)
    preferences: UserPreferences = Field(default_factory=UserPreferences)

class PintEconomy(BaseModel):
    users: Dict[str, UserData] = Field(default_factory=dict)

# Define the Pydantic model for the request body
class OweRequest(BaseModel):
    debtor: int
    creditor: int
    pint_number: str
    reason: str = Field(default="", max_length=200)  # Optional field with a max length of 200 characters