from pydantic import BaseModel

class UserPreferences(BaseModel):
    """Represents the preferences of a user."""
    use_unicode: bool = False
