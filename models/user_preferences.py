from pydantic import BaseModel

class UserPreferences(BaseModel):
    use_unicode: bool = False
