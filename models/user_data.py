from pydantic import BaseModel, Field

from models.user_debts import UserDebts
from models.user_preferences import UserPreferences

class UserData(BaseModel):
    """Represents a user's data in the system."""
    debts: UserDebts = Field(default_factory=UserDebts)
    preferences: UserPreferences = Field(default_factory=UserPreferences)
