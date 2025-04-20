# Imports
from fastapi import FastAPI, HTTPException, Depends
from fractions import Fraction
from datetime import datetime
import os
import json
from mixed_number_to_fraction import mixed_number_to_fraction
import logging
from OweRequest import OweRequest

# Setup 
logging.basicConfig(level=logging.DEBUG)

# Set up FastAPI
app = FastAPI()

DEBTS_FILE = 'PintDebts.json'

def get_debts():
    return load_debts()

def load_debts():
    if not os.path.exists(DEBTS_FILE):
        # Create an empty debts JSON structure if the file doesn't exist
        with open(DEBTS_FILE, 'w') as f:
            json.dump({}, f, indent=2)
        return {}
    try:
        with open(DEBTS_FILE, 'r') as f:
            raw = json.load(f)
    except json.JSONDecodeError:
        print("Error: Malformed JSON in debts file.")
        return {}
    
    debts = {}
    for debtor, creditors in raw.items():
        debts[debtor] = {}
        for creditor, entries in creditors.items():
            debts[debtor][creditor] = [
                {"amount": Fraction(entry["amount"]), "reason": entry["reason"], "timestamp": entry["timestamp"]}
                for entry in entries
            ]
    
    return debts

def save_debts(debts):
    to_save = {}
    for debtor, creditors in debts.items():
        if debtor not in to_save:
            to_save[debtor] = {}
        for creditor, entries in creditors.items():
            if creditor not in to_save[debtor]:
                to_save[debtor][creditor] = []

            # Append all debts for this creditor
            to_save[debtor][creditor].extend(
                {"amount": str(entry["amount"]), "reason": entry["reason"], "timestamp": entry["timestamp"]}
                for entry in entries
            )    

    # Save the updated debts to the file
    with open(DEBTS_FILE, "w") as f:
        json.dump(to_save, f, indent=2)

# Load debts at startup
debts = load_debts()

# /owe to add pint debts
@app.post("/owe")
async def add_pint_debt(request: OweRequest,
                        debts: dict = Depends(get_debts)):
    try:
        amount = mixed_number_to_fraction(request.pint_number.strip())
    except (ValueError, ZeroDivisionError):
        raise HTTPException(status_code=400, detail=f"Invalid pint amount {request.pint_number}. Use a number like 1, 0.5, or 1/3. Mixed fractions like 1 1/3 also allowed.")
    except (Exception):
        raise HTTPException(status_code=400, detail="Bad request {request.pint_number}, that's not good input.")
    #check in range
    if amount < 0:
        raise HTTPException(status_code=400, detail="Negative pints detected! That's ILLEGAL!")
    elif amount == 0:
        raise HTTPException(status_code=400, detail="As funny as zero pint debts would be, let's keep this to real debts for sanity's sake.")
    elif amount > 10:
        raise HTTPException(status_code=400, detail="Do you really need to add that many pints at once?")
    
    #check valid fraction
    if amount.denominator not in [1, 2, 3, 6]:
        raise HTTPException(status_code=400, detail="Woah there buckaroo, pints are quantized to 1/6 amounts.")

    #check if valid target to owe
    if request.debtor == request.creditor:
        raise HTTPException(status_code=400, detail="You can't owe yourself pints, that would be too confusing sorry.")
  
    timestamp = datetime.now().strftime("%d-%m-%Y")
    if str(request.debtor) not in debts:
        debts[str(request.debtor)] = {}
    if str(request.creditor) not in debts[str(request.debtor)]:
        debts[str(request.debtor)][str(request.creditor)] = []
    
    # Append the new debt to the list
    debts[str(request.debtor)][str(request.creditor)].append(
        {"amount": str(amount), "reason": request.reason, "timestamp": timestamp}
    )

    # Save the updated debts to the file
    save_debts(debts)
    return {"amount": str(amount), "reason": request.reason, "timestamp": timestamp}

# /pints to see your current pint debts
@app.get("/pints/{user_id}")
async def pints(user_id: int, debts: dict = Depends(get_debts)):
    # Prepare the response
    result = {"owed_by_you": {}, "total_owed_by_you": 0, "owed_to_you": {}, "total_owed_to_you": 0}
    total_owed_by_you = 0
    total_owed_to_you = 0

    # Check if the user owes debts to others
    user_id_str = str(user_id)
    if user_id_str in debts:
        for creditor_id, entries in debts[user_id_str].items():
            result["owed_by_you"][creditor_id] = [
                {"amount": str(entry["amount"]), "reason": entry["reason"], "timestamp": entry["timestamp"]}
                for entry in entries
            ]
            total_owed_by_you += sum(Fraction(entry["amount"]) for entry in entries)

    result["total_owed_by_you"] = str(total_owed_by_you)

    # Check if others owe debts to the user
    for debtor_id, creditors in debts.items():
        if user_id_str in creditors:
            if debtor_id not in result["owed_to_you"]:
                result["owed_to_you"][debtor_id] = []  # Initialize the debtor_id key
            result["owed_to_you"][debtor_id].extend(
                {"amount": str(entry["amount"]), "reason": entry["reason"], "timestamp": entry["timestamp"]}
                for entry in creditors[user_id_str]
            )
            total_owed_to_you += sum(Fraction(entry["amount"]) for entry in creditors[user_id_str])

    result["total_owed_to_you"] = str(total_owed_to_you)

    # If no debts are found, return an empty response
    if not result["owed_by_you"] and not result["owed_to_you"]:
        return {"message": "No debts found for this user. That's kind of cringe, get some pint debt bro."}

    return result

@app.get("/allpints")
async def all_pints(debts: dict = Depends(get_debts)):
    result = {}

    for debtor_id, creditors in debts.items():
        total_owed_by = sum(
            sum(Fraction(entry["amount"]) for entry in entries)
            for entries in creditors.values()
        )
        if debtor_id not in result:
            result[debtor_id] = {"owes": str(total_owed_by), "is_owed": "0"}

    for debtor_id, creditors in debts.items():
        for creditor_id, entries in creditors.items():
            total_owed_to = sum(Fraction(entry["amount"]) for entry in entries)
            if creditor_id not in result:
                result[creditor_id] = {"owes": "0", "is_owed": str(total_owed_to)}
            else:
                result[creditor_id]["is_owed"] = str(
                    Fraction(result[creditor_id]["is_owed"]) + total_owed_to
                )

    return result
