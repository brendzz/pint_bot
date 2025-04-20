# Imports
from fastapi import FastAPI, HTTPException, Depends
from fractions import Fraction
from datetime import datetime
from dotenv import load_dotenv
import os
import json
from mixed_number_to_fraction import mixed_number_to_fraction
import logging
from models_api import PintEconomy, UserData, DebtEntry, OweRequest, UserPreferences
from data_manager import load_data, save_data

# Setup 
logging.basicConfig(level=logging.DEBUG)
load_dotenv(".env")

# Set up FastAPI
app = FastAPI()

CURRENCY_NAME = os.environ.get("CURRENCY_NAME","pint")
QUANTIZED_FRACTIONS = os.environ.get("QUANTIZED_FRACTIONS","[1, 2, 3, 6]")
GET_DEBTS_COMMAND = os.environ.get("GET_DEBTS_COMMAND","pints")
GET_ALL_DEBTS_COMMAND = os.environ.get("GET_ALL_DEBTS_COMMAND","allpints")

# /owe to add pint debts
@app.post("/owe")
async def add_debt(request: OweRequest):
    data = load_data()
    debtor_id = str(request.debtor)
    creditor_id = str(request.creditor)
    #check if valid target to owe
    if debtor_id == creditor_id:
        raise HTTPException(status_code=400, detail=f"You can't owe yourself {CURRENCY_NAME}s, that would be too confusing sorry. The {CURRENCY_NAME} economy is a complex system, and we don't want to break it.")
  
    try:
        amount = mixed_number_to_fraction(request.pint_number.strip())
    except (ValueError, ZeroDivisionError):
        raise HTTPException(status_code=400, detail=f"Invalid {CURRENCY_NAME} amount {request.pint_number}. Use a number like 1, 0.5, or 1/3. Mixed fractions like 1 1/3 also allowed.")
    except (Exception):
        raise HTTPException(status_code=400, detail="Bad request {request.pint_number}, that's not good input.")
    #check in range
    if amount < 0:
        raise HTTPException(status_code=400, detail="Negative {CURRENCY_NAME}s detected! That's ILLEGAL!")
    elif amount == 0:
        raise HTTPException(status_code=400, detail="As funny as zero {CURRENCY_NAME} debts would be, let's keep this to real debts for sanity's sake.")
    elif amount > 10:
        raise HTTPException(status_code=400, detail="Do you really need to add that many {CURRENCY_NAME}s at once?")
    #check valid fraction
    if amount.denominator not in [1, 2, 3, 6]:
        raise HTTPException(status_code=400, detail="Woah there buckaroo, {CURRENCY_NAME} are quantized to 1/6 amounts.")
    
     # Get or create the debtor's data
    if debtor_id not in data.users:
        data.users[debtor_id] = UserData()

    debtor_data = data.users[debtor_id]
    
   # Add the debt
    if creditor_id not in debtor_data.debts.creditors:
        debtor_data.debts.creditors[creditor_id] = []

    debtor_data.debts.creditors[creditor_id].append(
        DebtEntry(amount=amount, reason=request.reason, timestamp=datetime.now().strftime("%d-%m-%Y"))
    )

    # Save the updated data
    save_data(data)

    return {"amount": str(amount), "reason": request.reason, "timestamp": datetime.now().strftime("%d-%m-%Y")}

# /pints to see your current pint debts
@app.get(f"/{GET_DEBTS_COMMAND}/{{user_id}}")
async def get_debts(user_id: int):
    data = load_data()
    user_id_str = str(user_id)

    # initial check if user has debts they owe
    if user_id_str not in data.users:
        return {"message": "No debts found owed to or from this user. That's kind of cringe, get some {CURRENCY_NAME} debt bro."}
   
    user_data = data.users[user_id_str]
     # Prepare the response
    result = {"owed_by_you": {},
              "total_owed_by_you": 0, 
              "owed_to_you": {}, 
              "total_owed_to_you": 0}

    # Debts owed by the user
    for creditor_id, entries in user_data.debts.creditors.items():
        result["owed_by_you"][creditor_id] = [
            {"amount": str(entry.amount), "reason": entry.reason, "timestamp": entry.timestamp}
            for entry in entries
        ]
    result["total_owed_by_you"] += sum(entry.amount for entry in entries)

    # Debts owed to the user
    for debtor_id, user in data.users.items():
        if user_id_str in user.debts.creditors:
            if debtor_id not in result["owed_to_you"]:
                result["owed_to_you"][debtor_id] = []
            result["owed_to_you"][debtor_id].extend(
                {"amount": str(entry.amount), "reason": entry.reason, "timestamp": entry.timestamp}
                for entry in user.debts.creditors[user_id_str]
            )
    result["total_owed_to_you"] += sum(entry.amount for entry in user.debts.creditors[user_id_str])

    # If no debts are found, return an empty response
    if not result["owed_by_you"] and not result["owed_to_you"]:
        return {"message": f"No debts found owed to or from this user. That's kind of cringe, get some {CURRENCY_NAME} debt bro."}

    return result

@app.get(f"/{GET_ALL_DEBTS_COMMAND}")
async def get_all_debts():
    data = load_data()
    result = {}

    for debtor_id, debtor_data in data.users.items():
        total_owed_by = Fraction(0)
        for creditor_id, entries in debtor_data.debts.creditors.items():
            total_owed_by += sum(entry.amount for entry in entries)
        if debtor_id not in result:
            result[debtor_id] = {"owes": str(total_owed_by), "is_owed": "0"}

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

    return result

@app.post("/settle")
async def settle_debt(request: dict):
    data=load_data
    debtor_id = str(request["debtor"])
    creditor_id = str(request["creditor"])
    pint_number = Fraction(request["pint_number"])

    if pint_number < 0:
        raise HTTPException(status_code=400, detail="A negative? Really? Please use /owe to add your debts instead of trying to settle for negatives.")
    elif pint_number == 0:
        raise HTTPException(status_code=400, detail=f"The {CURRENCY_NAME} economy can only function with real valid transactions. Settling zero {CURRENCY_NAME}s is not that bro.")

    if debtor_id not in data.users or creditor_id not in data.users[debtor_id].debts.creditors:
        raise HTTPException(status_code=400, detail=f"You don't owe that person any debts. The {CURRENCY_NAME} economy cannot function without debts! Please get some debts to avoid the imminent financial crisis!")

    # Settle debts starting with the oldest
     # Settle debts starting with the oldest
    debtor_data = data.users[debtor_id]
    creditor_entries = debtor_data.debts.creditors[creditor_id]
    remaining_to_settle = pint_number
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
            entry.amount = entry_amount - remaining_to_settle
            updated_entries.append(entry)
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

    return {
        "settled_amount": str(settled_amount),
        "remaining_amount": str(max(remaining_to_settle, 0)),
    }

@app.post("/set_preference")
async def set_preference(user_id: int, use_unicode: bool):
    data = load_data()
    user_id_str = str(user_id)

    if user_id_str not in data.users:
        data.users[user_id_str] = UserData()

    data.users[user_id_str].preferences.use_unicode = use_unicode
    save_data(data)

    return {"message": f"Preference for Unicode fractions set to {use_unicode}."}