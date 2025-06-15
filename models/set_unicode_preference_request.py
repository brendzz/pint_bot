from pydantic import BaseModel

class SetUnicodePreferenceRequest(BaseModel):
    """Request model for setting a user's Unicode preference."""
    use_unicode: bool
