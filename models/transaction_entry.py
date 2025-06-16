from typing import Literal
from fractions import Fraction
from datetime import datetime, timezone
from pydantic import BaseModel, Field, field_validator

class TransactionEntry(BaseModel):
    """Details of a debt transaction."""
    type: Literal["owe", "settle"]
    debtor: str
    creditor: str
    amount: Fraction
    reason: str = ""
    timestamp: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
    )

    @field_validator("amount", mode="before")
    @classmethod
    def parse_amount(cls, v):
        """Convert amount to Fraction."""
        if isinstance(v, Fraction):
            return v
        return Fraction(str(v))

    def model_dump(self, *args, **kwargs):
        # Override to serialize Fraction as string
        d = super().model_dump(*args, **kwargs)
        d["amount"] = str(self.amount)
        return d
