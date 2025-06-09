from pydantic import BaseModel
from models.transaction_entry import TransactionEntry

class TransactionsData(BaseModel):
    """Data structure for managing transactions."""
    transactions: list[TransactionEntry]
