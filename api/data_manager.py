import json
import os
from models import PintEconomy

DATA_FILE = os.environ.get("DATA_FILE","PintEconomy.json")

def load_data() -> PintEconomy:
    """Load the PintEconomy data from a JSON file."""
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
    """Save the PintEconomy data to a JSON file."""
    with open(DATA_FILE, "w") as f:
        json.dump(data.model_dump(), f, indent=2)