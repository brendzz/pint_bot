from datetime import datetime
from fractions import Fraction
from models import DebtEntry, UserData

DATE_FORMAT = "%d-%m-%Y"

def serialize_debt_entry(entry: DebtEntry) -> dict:
    """Serialize a DebtEntry object to a dictionary."""
    return {
        "amount": str(entry.amount),
        "reason": entry.reason,
        "timestamp": entry.timestamp,
    }

def sum_debts(entries: list[DebtEntry]) -> Fraction:
    """Sum the amounts of all debt entries."""
    return sum(Fraction(entry.amount) for entry in entries)

def current_timestamp() -> str:
    """Get the current timestamp in the specified format."""
    return datetime.now().strftime(DATE_FORMAT)

def get_or_create_user(data, user_id: str) -> UserData:
    """Get or create a user record for the given user_id."""
    if user_id not in data.users:
        data.users[user_id] = UserData()
    return data.users[user_id]