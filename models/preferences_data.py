from typing import Dict
from pydantic import BaseModel
from models.user_preferences import UserPreferences

class PreferencesData(BaseModel):
    """Data structure for managing user preferences."""
    users: Dict[str, UserPreferences]
