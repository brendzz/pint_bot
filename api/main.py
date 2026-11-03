# Imports
"""FastAPI for managing pint debts between users."""
from datetime import date, datetime, timedelta, timezone
from fractions import Fraction
import logging
from typing import Optional
from fastapi import FastAPI, HTTPException, Query
import api.config as config
import api.fraction_functions as fraction_functions
from api.data_manager import (
    add_debt as add_debt_to_db,
    append_transaction,
    get_transactions as get_transactions_from_db,
    get_unicode_preference as get_unicode_preference_from_db,
    load_debts,
    settle_debt as settle_debt_in_db,
    set_unicode_preference as set_unicode_preference_in_db,
)
from api.utilities.debt_helpers import (
    current_timestamp,
    debts_between,
    debts_owed_by,
    debts_owed_to,
)
from api.utilities.transaction_helpers import normalize_transaction_type
from models import (
    DebtEntry,
    OweRequest,
    SettleRequest,
    SetUnicodePreferenceRequest,
    TransactionEntry
)

# Setup
logging.basicConfig(level=logging.DEBUG)

# Set up FastAPI
app = FastAPI()

NO_DEBTS_MESSAGE = "No debts found owed to or from this user."
HTTP_BAD_REQUEST_CODE = 400

@app.get("/health", status_code=200)
async def health_check():
    """Health check endpoint."""
    return {"status": "ok"}

@app.get("/transactions")
async def get_transactions(
    start_date: date = Query(default_factory=lambda: date.today() - timedelta(days=config.TRANSACTIONS_DEFAULT_TIME_PERIOD)),
    end_date: date = Query(default_factory=date.today),
    user_id: Optional[str] = None,
    type: Optional[str] = Query(None),
):
    
    """
    Get all transactions in a date range (default: last 30 days).
    Optionally filtered by type and/or user.
    """
    transaction_type = normalize_transaction_type(type)
    if transaction_type == "cashout":
        transaction_type = "settle"

    if start_date > end_date:
        raise HTTPException(
            status_code=HTTP_BAD_REQUEST_CODE,
            detail="VALIDATION_ERROR"
        )

    # Convert date to datetime boundaries
    start_datetime = datetime.combine(start_date, datetime.min.time(), tzinfo=timezone.utc)
    end_datetime = datetime.combine(end_date, datetime.max.time(), tzinfo=timezone.utc)

    transactions = get_transactions_from_db(
        start=start_datetime,
        end=end_datetime,
        user_id=user_id,
        transaction_type=transaction_type,
    )

    # Convert each transaction to a dictionary for JSON serialization
    return {
        "start_date": str(start_date),
        "end_date": str(end_date),
        "transactions": [transaction.model_dump() for transaction in transactions]
    }

@app.post("/debts")
async def add_debt(request: OweRequest):
    """Add pint debts between a pair of users."""

    debtor_id = str(request.debtor)
    creditor_id = str(request.creditor)
    # Check if valid target to owe
    if debtor_id == creditor_id:
        raise HTTPException(status_code=HTTP_BAD_REQUEST_CODE, detail="CANNOT_OWE_SELF")

    amount = fraction_functions.mixed_number_to_fraction(request.amount.strip())

    # Checks
    fraction_functions.check_in_range(amount, settling=False)
    
    if config.QUANTIZE_OWING_DEBTS:
        fraction_functions.check_quantization(amount)

    try:
        debt_entry = DebtEntry(
            amount=amount,
            reason=request.reason,
            timestamp=current_timestamp()
        )
    except ValueError as exc:
        raise HTTPException(status_code=HTTP_BAD_REQUEST_CODE, detail="EXCEEDS_MAXIMUM") from exc

    add_debt_to_db(debtor_id, creditor_id, debt_entry)

    transaction_entry= TransactionEntry(
        type = "owe",
        debtor = debtor_id,
        creditor = creditor_id,
        amount = amount,
        reason = request.reason
    )

    # Append the transaction entry
    append_transaction(transaction_entry)

    return {
        "amount": str(amount),
        "reason": request.reason,
        "timestamp": current_timestamp()
    }

@app.get("/users/{user_id}/debts")
async def get_debts(user_id: str):
    """See a user's current pint debts."""
    data = load_debts()

    owed_by_you, total_owed_by_you = debts_owed_by(data, user_id)
    owed_to_you, total_owed_to_you = debts_owed_to(data, user_id)

    if not owed_by_you and not owed_to_you:
        return {"message": NO_DEBTS_MESSAGE}

    return {
        "owed_by_you": owed_by_you,
        "total_owed_by_you": str(total_owed_by_you),
        "owed_to_you": owed_to_you,
        "total_owed_to_you": str(total_owed_to_you),
    }

@app.get("/debts")
async def get_all_debts():
    """See all current debts."""
    debts_data = load_debts()

    result = {}
    total_in_circulation = Fraction(0)
    summary = {}

    for debtor_id, debtor_data in debts_data.debtors.items():
        for creditor_id, entries in debtor_data.creditors.items():
            amount = sum(entry.amount for entry in entries)
            total_in_circulation += amount

            # Update debtor's "owes"
            summary.setdefault(debtor_id, {"owes": Fraction(0), "is_owed": Fraction(0)})
            summary[debtor_id]["owes"] += amount

            # Update creditor's "is_owed"
            summary.setdefault(creditor_id, {"owes": Fraction(0), "is_owed": Fraction(0)})
            summary[creditor_id]["is_owed"] += amount

    # Sort by default in config
    if config.SORT_OWES_FIRST:
        sort_key=lambda item: item[1]["owes"]
    else:
        sort_key=lambda item: item[1]["is_owed"]

    sorted_items = sorted(
            summary.items(),
            key=sort_key,
            reverse=True
        )

    result = {
        user_id: {
            "owes": str(summary_data["owes"]),
            "is_owed": str(summary_data["is_owed"]),
        }
        for user_id, summary_data in sorted_items
    }
    result["total_in_circulation"] = str(total_in_circulation)
    return result

@app.get("/debts/between")
async def debts_with_user(requester_id: str, target_id: str):
    """See current debts between the requester and one other user."""
    data = load_debts()

    debts = debts_between(data, requester_id, target_id)

    # If no debts are found, return an empty response
    if not debts["owed_by_you"] and not debts["owed_to_you"]:
        return {"message": NO_DEBTS_MESSAGE}

    # Convert totals back to strings for the response
    debts["total_owed_by_you"] = str(debts["total_owed_by_you"])
    debts["total_owed_to_you"] = str(debts["total_owed_to_you"])

    return debts

@app.patch("/debts")
async def settle_debt(request: SettleRequest):
    """Settle debt between a pair of users."""
    debtor_id = str(request.debtor)
    creditor_id = str(request.creditor)

    # Validate and parse the pint number
    amount = fraction_functions.mixed_number_to_fraction(request.amount.strip())

    # Validate pint number constraints
    fraction_functions.check_in_range(amount, settling=True)

    if config.QUANTIZE_SETTLING_DEBTS:
        fraction_functions.check_quantization(amount)

    settlement = settle_debt_in_db(debtor_id, creditor_id, amount)
    if settlement is None:
        raise HTTPException(
            status_code=HTTP_BAD_REQUEST_CODE,
            detail="NO_DEBTS_FOUND"
        )

    transaction_entry= TransactionEntry(
        type = "settle",
        debtor = debtor_id,
        creditor = creditor_id,
        amount = settlement.settled_amount,
        reason = request.reason
    )

    # Append the transaction entry
    append_transaction(transaction_entry)

    return {
        "settled_amount": str(settlement.settled_amount),
        "remaining_amount": str(settlement.remaining_amount),
        "reason": request.reason,
        "timestamp": current_timestamp()
    }

@app.get("/users/{user_id}/unicode_preference")
async def get_unicode_preference(user_id: str) -> bool:
    """Get a user's preference on whether they want fractions to be displayed in Unicode format."""
    return get_unicode_preference_from_db(user_id)

@app.post("/users/{user_id}/unicode_preference")
async def set_unicode_preference(user_id: str, request: SetUnicodePreferenceRequest):
    """Set a user's preference on whether they want fractions to be displayed in Unicode format."""
    unicode_preference = request.use_unicode
    set_unicode_preference_in_db(user_id, unicode_preference)

    return {"message": f"Preference for Unicode fractions set to {unicode_preference}."}

@app.get("/settings")
async def get_settings():
    """Get current bot settings."""
    # You can customize which config values to expose
    return {
        "MAXIMUM_DEBT_CHARACTER_LIMIT": config.MAXIMUM_DEBT_CHARACTER_LIMIT,
        "MAXIMUM_PER_DEBT": config.MAXIMUM_PER_DEBT,
        "SMALLEST_UNIT": str(config.SMALLEST_UNIT),
        "QUANTIZE_SETTLING_DEBTS": config.QUANTIZE_SETTLING_DEBTS,
        "QUANTIZE_OWING_DEBTS": config.QUANTIZE_OWING_DEBTS,
        "SORT_OWES_FIRST": config.SORT_OWES_FIRST
    }