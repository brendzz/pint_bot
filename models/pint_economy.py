from pydantic import BaseModel, Field
from typing import Dict

from models.user_data import UserData

class PintEconomy(BaseModel):
    """Main data structure for the debt management system."""
    users: Dict[str, UserData] = Field(default_factory=dict)
