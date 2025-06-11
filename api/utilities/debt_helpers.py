from datetime import datetime
from fractions import Fraction
from models import DebtEntry

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

def build_debt_summary(entries: list[DebtEntry]) -> tuple[list[dict], Fraction]:
    """Returns serialized debt entries and their total sum."""
    serialized = [serialize_debt_entry(e) for e in entries]
    total = sum_debts(entries)
    return serialized, total

def debts_owed_by(data, user_id: str):
    """Returns a summary of debts the user owes."""
    owes = {}
    total = Fraction(0)
    if user_id in data.debtors:
        for creditor_id, entries in data.debtors[user_id].creditors.items():
            serialized, subtotal = build_debt_summary(entries)
            owes[creditor_id] = serialized
            total += subtotal

    # Sort creditors by total owed (descending by default)
    sorted_owes = dict(
        sorted(
            owes.items(),
            key=lambda item: sum(Fraction(e["amount"]) for e in item[1]),
            reverse=True
        )
    )

    return sorted_owes, total

def debts_owed_to(data, user_id: str):
    """Returns a summary of debts owed to the user."""
    owed = {}
    total = Fraction(0)
    for debtor_id, user in data.debtors.items():
        if user_id in user.creditors:
            serialized, subtotal = build_debt_summary(user.creditors[user_id])
            if debtor_id not in owed:
                owed[debtor_id] = []
            owed[debtor_id].extend(serialized)
            total += subtotal

    # Sort debtors by total owed (descending by default)
    sorted_owed = dict(
        sorted(
            owed.items(),
            key=lambda item: sum(Fraction(e["amount"]) for e in item[1]),
            reverse=True
        )
    )
    return sorted_owed, total

def debts_to(data, from_user_id: str, to_user_id: str):
    """Returns debts from one user to another."""
    owed = {}
    total = Fraction(0)

    if from_user_id in data.debtors:
        requesters_debts = data.debtors[from_user_id].creditors
        if to_user_id in requesters_debts:
            debts = requesters_debts[to_user_id]
            owed, total = build_debt_summary(debts)

    return owed, total

def debts_between(data, user_id1: str, user_id2: str):
    """Returns a summary of debts between two users."""
    owed_by_you, total_owed_by_you = debts_to(data, user_id1, user_id2)
    owed_to_you, total_owed_to_you = debts_to(data, user_id2, user_id1)

    result = {
        "owed_by_you": owed_by_you,
        "total_owed_by_you": total_owed_by_you,
        "owed_to_you": owed_to_you,
        "total_owed_to_you": total_owed_to_you
    }

    return result

def settle_debts_between_users(entries: list[DebtEntry], amount_to_settle: Fraction) -> tuple[list[DebtEntry], Fraction]:
    """Settle debts in FIFO order. Returns updated entries and settled amount."""
    remaining = amount_to_settle
    settled = Fraction(0)
    updated_entries = []

    for entry in entries:
        if remaining <= 0:
            updated_entries.append(entry)
            continue

        if entry.amount <= remaining:
            # Fully settle this entry
            settled += entry.amount
            remaining -= entry.amount
        else:
            # Partially settle this entry
            settled += remaining
            updated_entries.append(DebtEntry(
                amount=entry.amount - remaining,
                reason=entry.reason,
                timestamp=entry.timestamp
            ))
            remaining = 0

    return updated_entries, settled
