# Imports
"""FastAPI for managing pint debts between users."""
from fractions import Fraction
import logging
from fastapi import FastAPI, HTTPException
import api.config as config
import api.fraction_functions as fractions
from api.data_manager import load_data, save_data
from api.utilities.debt_helpers import (
    current_timestamp,
    debts_between,
    debts_owed_by,
    debts_owed_to,
    get_or_create_user
)
from models import (
    DebtEntry,
    OweRequest,
    SettleRequest,
    SetUnicodePreferenceRequest
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

@app.post("/debts")
async def add_debt(request: OweRequest):
    """Add pint debts between a pair of users."""

    data = load_data()
    debtor_id = str(request.debtor)
    creditor_id = str(request.creditor)
    # Check if valid target to owe
    if debtor_id == creditor_id:
        raise HTTPException(status_code=HTTP_BAD_REQUEST_CODE, detail="CANNOT_OWE_SELF")

    amount = fractions.mixed_number_to_fraction(request.amount.strip())

    # Checks
    fractions.check_in_range(amount, settling=False)
    fractions.check_quantization(amount)

    # Get or create the debtor's data
    debtor = get_or_create_user(data, debtor_id)

    # Add the debt
    if creditor_id not in debtor.debts.creditors:
        debtor.debts.creditors[creditor_id] = []

    try:
        {
            debtor.debts.creditors[creditor_id].append(
                DebtEntry(
                    amount=amount,
                    reason=request.reason,
                    timestamp=current_timestamp()
                )
            )
        }
    except ValueError as exc:
        raise HTTPException(status_code=HTTP_BAD_REQUEST_CODE, detail="EXCEEDS_MAXIMUM") from exc
    # Save the updated data
    save_data(data)

    return {
        "amount": str(amount),
        "reason": request.reason,
        "timestamp": current_timestamp()
    }

@app.get("/users/{user_id}/debts")
async def get_debts(user_id: str):
    """See a user's current pint debts."""
    data = load_data()

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
    data = load_data()

    result = {}
    total_in_circulation= Fraction(0)
    # Iterate over all users to calculate debts owed by them
    for debtor_id, debtor_data in data.users.items():
        total_owed_by = Fraction(0)
        for creditor_id, entries in debtor_data.debts.creditors.items():
            total_owed_by += sum(entry.amount for entry in entries)
        if debtor_id not in result:
            result[debtor_id] = {"owes": str(total_owed_by), "is_owed": "0"}
        total_in_circulation += total_owed_by
     # Iterate over all users to calculate debts owed to them
    for debtor_id, debtor_data in data.users.items():
        for creditor_id, entries in debtor_data.debts.creditors.items():
            total_owed_to = sum(entry.amount for entry in entries)
            if creditor_id not in result:
                result[creditor_id] = {"owes": "0", "is_owed": str(total_owed_to)}
            else:
                result[creditor_id]["is_owed"] = str(
                    Fraction(result[creditor_id]["is_owed"]) + total_owed_to
                )
    result["total_in_circulation"] = str(total_in_circulation)
    return result

@app.get("/debts/between")
async def debts_with_user(requester_id: str, target_id: str):
    """See current debts between the requester and one other user."""
    data = load_data()

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
    data = load_data()
    debtor_id = str(request.debtor)
    creditor_id = str(request.creditor)

    # Validate and parse the pint number
    amount = fractions.mixed_number_to_fraction(request.amount.strip())

    # Validate pint number constraints
    fractions.check_in_range(amount, settling=True)

    if config.QUANTIZE_SETTLING_DEBTS is True:
        fractions.check_quantization(amount)

    # Check if the debtor owes the creditor
    if debtor_id not in data.users or creditor_id not in data.users[debtor_id].debts.creditors:
        raise HTTPException(
            status_code=HTTP_BAD_REQUEST_CODE,
            detail="NO_DEBTS_FOUND"
        )

    # Settle debts starting with the oldest
    debtor_data = data.users[debtor_id]
    creditor_entries = debtor_data.debts.creditors[creditor_id]
    remaining_to_settle = amount # Track amount left to settle in this transaction
    settled_amount = Fraction(0)
    updated_entries = []

    for entry in creditor_entries:
        entry_amount = entry.amount
        if remaining_to_settle <= 0:
            updated_entries.append(entry)  # Keep remaining debts
            continue

        if entry_amount <= remaining_to_settle:
            # Fully settle this entry
            settled_amount += entry_amount
            remaining_to_settle -= entry_amount
        else:
            # Partially settle this entry
            settled_amount += remaining_to_settle
            updated_entry = DebtEntry(
                amount=entry_amount - remaining_to_settle,
                reason=entry.reason,
                timestamp=entry.timestamp
            )
            updated_entries.append(updated_entry)
            remaining_to_settle = 0

    # Update debts
    if updated_entries:
        debtor_data.debts.creditors[creditor_id] = updated_entries
    else:
        del debtor_data.debts.creditors[creditor_id]  # Remove creditor if all debts are settled

    if not debtor_data.debts.creditors:
        del data.users[debtor_id]  # Remove debtor if no debts remain

    # Save the updated data
    save_data(data)

    # Calculate the total remaining debt for the creditor
    total_remaining_debt = sum(entry.amount for entry in updated_entries)

    return {
        "settled_amount": str(settled_amount),
        "remaining_amount": str(total_remaining_debt),
    }

@app.get("/users/{user_id}/unicode_preference")
async def get_unicode_preference(user_id: str):
    """Get a user's preference on whether they want fractions to be displayed in Unicode format."""
    data = load_data()

    # Check if the user exists in the data
    if user_id not in data.users:
        return {"use_unicode": False}  # Default value if the user does not exist

    # Retrieve the user's Unicode preference or return the default value
    use_unicode = getattr(data.users[user_id].preferences, "use_unicode", False)

    return {"use_unicode": use_unicode}

@app.post("/users/{user_id}/unicode_preference")
async def set_unicode_preference(user_id: str, request: SetUnicodePreferenceRequest):
    """Set a user's preference on whether they want fractions to be displayed in Unicode format."""
    data = load_data()
    user = get_or_create_user(data, user_id)

    unicode_preference = request.use_unicode
    user.preferences.use_unicode = unicode_preference
    save_data(data)

    return {"message": f"Preference for Unicode fractions set to {unicode_preference}."}
