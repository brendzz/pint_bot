import json
import os
from models import PintEconomy
import datetime
from uuid import uuid4 as uuid

DATA_FILE = os.environ.get("DATA_FILE","PintEconomy.json")
LOG_PATH = os.environ.get("LOG_PATH", "logs")

def load_data() -> PintEconomy:
    if not os.path.exists(DATA_FILE):
        # Create an empty data structure if the file doesn't exist
        return PintEconomy()
    try:
        with open(DATA_FILE, "r") as f:
            raw_data = json.load(f)
            return PintEconomy.model_validate(raw_data)
    except (json.JSONDecodeError, ValueError):
        print("Error: Malformed JSON in data file.")
        return PintEconomy()

def save_data(data: PintEconomy):
    with open(DATA_FILE, "w") as f:
        json.dump(data.model_dump(), f, indent=2)

def save_transaction(transaction: str, pint_quantity: str, debtor_id: str, creditor_id: str, reason: str):
    now = datetime.datetime.now().isoformat()
    filename: str = os.path.join(LOG_PATH, f"{now}-{uuid().hex}.txt")
    with open(filename, "w") as logfile:
        logfile.writelines([
            f"type={transaction}\n",
            f"amount={pint_quantity}\n",
            f"debtor={debtor_id}\n",
            f"creditor={creditor_id}\n",
            f"reason={reason}\n"
        ])
