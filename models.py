from pydantic import BaseModel, Field

# Define the Pydantic model for the request body
class OweRequest(BaseModel):
    debtor: int
    creditor: int
    pint_number: str
    reason: str = Field(default="", max_length=200)  # Optional field with a max length of 200 characters