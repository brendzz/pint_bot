from pydantic import BaseModel

class SettleRequest(BaseModel):
    debtor: int
    creditor: int
    amount: str