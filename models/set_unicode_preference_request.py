from pydantic import BaseModel

class SetUnicodePreferenceRequest(BaseModel):
    """Request model for setting a user's Unicode preference."""
    user_id: str
    use_unicode: bool
