from pydantic import BaseModel, Field
from typing import List, Dict
from fractions import Fraction
import os

MAXIMUM_DEBT_CHARACTER_LIMIT = int(os.environ.get("MAXIMUM_DEBT_CHARACTER_LIMIT", "200")) 

class DebtEntry(BaseModel):
    amount: Fraction = Field(gt=0, le=10)
    reason: str = Field(default="",max_length=MAXIMUM_DEBT_CHARACTER_LIMIT)
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

#Requests

# Define the Pydantic model for the request body
class OweRequest(BaseModel):
    debtor: int
    creditor: int
    amount: str
    reason: str = Field(default="", max_length=MAXIMUM_DEBT_CHARACTER_LIMIT)  # Optional field with a max length of 200 characters

class SettleRequest(BaseModel):
    debtor: int
    creditor: int
    amount: str  # Fraction as a string

class SetUnicodePreferenceRequest(BaseModel):
    user_id: int
    use_unicode: bool