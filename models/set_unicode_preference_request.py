from pydantic import BaseModel

class SetUnicodePreferenceRequest(BaseModel):
    user_id: str
    use_unicode: bool
