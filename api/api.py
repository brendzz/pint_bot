# Imports
from fastapi import FastAPI, HTTPException, Depends
from fractions import Fraction
from datetime import datetime
from api.config import load_config
from fraction_functions import mixed_number_to_fraction #,calculate_allowed_denominators
import logging
from data_manager import load_data, save_data
from models.models import UserData, DebtEntry, OweRequest, SettleRequest, SetUnicodePreferenceRequest

# Setup 
logging.basicConfig(level=logging.DEBUG)
CONFIG = load_config()

SMALLEST_UNIT = CONFIG["SMALLEST_UNIT"]
QUANTIZE_SETTLING_DEBTS = CONFIG["QUANTIZE_SETTLING_DEBTS"]
GET_DEBTS_COMMAND = CONFIG["GET_DEBTS_COMMAND"]
GET_ALL_DEBTS_COMMAND = CONFIG["GET_ALL_DEBTS_COMMAND"]
MAXIMUM_PER_DEBT = CONFIG["MAXIMUM_PER_DEBT"]

# Set up FastAPI
app = FastAPI()

@app.post("/owe")
async def add_debt(request: OweRequest):
    """Add pint debts between a pair of users."""

    data = load_data()
    debtor_id = str(request.debtor)
    creditor_id = str(request.creditor)
    # Check if valid target to owe
    if debtor_id == creditor_id:
        raise HTTPException(status_code=400, detail="CANNOT_OWE_SELF")
  
    try:
        amount = mixed_number_to_fraction(request.amount.strip())
    except (ValueError, ZeroDivisionError):
        raise HTTPException(status_code=400, detail="INVALID_AMOUNT")
    except (Exception):
        raise HTTPException(status_code=400, detail="BAD_REQUEST")
    # Check in range
    if amount < 0:
        raise HTTPException(status_code=400, detail="NEGATIVE_AMOUNT")
    elif amount == 0:
        raise HTTPException(status_code=400, detail="ZERO_AMOUNT")
    elif amount > Fraction(MAXIMUM_PER_DEBT):
        raise HTTPException(status_code=400, detail="EXCEEDS_MAXIMUM")
    
    # Check if the fraction is quantized to the smallest unit using modulo
    smallest_unit = Fraction(SMALLEST_UNIT)

    if (amount % smallest_unit != 0):
        raise HTTPException(
            status_code=400,
            detail="NOT_QUANTIZED"
        )

     # Get or create the debtor's data
    if debtor_id not in data.users:
        data.users[debtor_id] = UserData()

    debtor_data = data.users[debtor_id]
    
  
   # Add the debt
    if creditor_id not in debtor_data.debts.creditors:
        debtor_data.debts.creditors[creditor_id] = []

    try:
        {
    debtor_data.debts.creditors[creditor_id].append(
        DebtEntry(amount=amount, reason=request.reason, timestamp=datetime.now().strftime("%d-%m-%Y"))
    )
        }
    except ValueError:
        raise HTTPException(status_code=400, detail="EXCEEDS_MAXIMUM")
    # Save the updated data
    save_data(data)

    return {"amount": str(amount), "reason": request.reason, "timestamp": datetime.now().strftime("%d-%m-%Y")}

@app.get(f"/{GET_DEBTS_COMMAND}/{{user_id}}")
async def get_debts(user_id: str):
    """See your current pint debts."""
    data = load_data()
    
     # Prepare the response
    result = {"owed_by_you": {},
              "total_owed_by_you": 0, 
              "owed_to_you": {}, 
              "total_owed_to_you": 0
      }  # Include the user's preference}
    
    # Check if the user exists in the data
    if user_id in data.users:
        user_data = data.users[user_id]

        # Debts owed by the user
        for creditor_id, entries in user_data.debts.creditors.items():
            if not isinstance(entries, list):
                raise TypeError(f"Expected 'entries' to be a list, but got {type(entries)}")
            result["owed_by_you"][creditor_id] = [
                {
                    "amount": str(entry.amount),
                    "reason": entry.reason,
                    "timestamp": entry.timestamp,
                }
                for entry in entries
            ]
            # Convert amount to Fraction for summation
            result["total_owed_by_you"] += sum(Fraction(entry.amount) for entry in entries)

    # Check if the user is a creditor in other users' debts
    for debtor_id, user in data.users.items():
        if user_id in user.debts.creditors:
            if debtor_id not in result["owed_to_you"]:
                result["owed_to_you"][debtor_id] = []
            result["owed_to_you"][debtor_id].extend(
                {
                    "amount": str(entry.amount),
                    "reason": entry.reason,
                    "timestamp": entry.timestamp,
                }
                for entry in user.debts.creditors[user_id]
            )
            # Convert amount to Fraction for summation
            result["total_owed_to_you"] += sum(Fraction(entry.amount) for entry in user.debts.creditors[user_id])

    # If no debts are found, return an empty response
    if not result["owed_by_you"] and not result["owed_to_you"]:
        return {"message": "No debts found owed to or from this user."}

    # Convert totals back to strings for the response
    result["total_owed_by_you"] = str(result["total_owed_by_you"])
    result["total_owed_to_you"] = str(result["total_owed_to_you"])

    return result

@app.get(f"/{GET_ALL_DEBTS_COMMAND}")
async def get_all_debts():
    """To see all current debts between users."""
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

@app.post("/settle")
async def settle_debt(request: SettleRequest):
    """Settle debt between a pair of users."""
    data = load_data()
    debtor_id = str(request.debtor)
    creditor_id = str(request.creditor)

    # Validate and parse the pint number
    try:
        amount = Fraction(request.amount.strip())
    except ValueError:
        raise HTTPException(status_code=400, detail="INVALID_AMOUNT")

    # Validate pint number constraints
    if amount < 0:
        raise HTTPException(status_code=400, detail="NEGATIVE_AMOUNT")
    elif amount == 0:
        raise HTTPException(status_code=400, detail="ZERO_AMOUNT")

    # Check if the fraction is quantized to the smallest unit using modulo
    smallest_unit = Fraction(SMALLEST_UNIT)

    if QUANTIZE_SETTLING_DEBTS == True and (amount % smallest_unit != 0):
        raise HTTPException(
            status_code=400,
            detail="NOT_QUANTIZED"
        )
    
    # Check if the debtor owes the creditor
    if debtor_id not in data.users or creditor_id not in data.users[debtor_id].debts.creditors:
        raise HTTPException(
            status_code=400,
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

@app.get("/get_unicode_preference/{user_id}")
async def get_unicode_preference(user_id: str):
    """Get a user's preference on whether they want fractions to be displayed in Unicode format."""
    data = load_data()

    # Check if the user exists in the data
    if user_id not in data.users:
        return {"use_unicode": False}  # Default value if the user does not exist

    # Retrieve the user's Unicode preference or return the default value
    use_unicode = getattr(data.users[user_id].preferences, "use_unicode", False)

    return {"use_unicode": use_unicode}

@app.post("/set_unicode_preference")
async def set_unicode_preference(request: SetUnicodePreferenceRequest):
    """Set a user's preference on whether they want fractions to be displayed in Unicode format."""
    data = load_data()
    user_id = str(request.user_id)
    use_unicode = request.use_unicode

    if user_id not in data.users:
        data.users[user_id] = UserData()

    data.users[user_id].preferences.use_unicode = use_unicode
    save_data(data)

    return {"message": f"Preference for Unicode fractions set to {use_unicode}."}