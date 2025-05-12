import json
import os
import api.config as config
from models import PintEconomy

def load_data() -> PintEconomy:
    """Load the PintEconomy data from a JSON file."""
    if not os.path.exists(config.DATA_FILE):
        # Create an empty data structure if the file doesn't exist
        return PintEconomy()
    try:
        with open(config.DATA_FILE, "r") as f:
            raw_data = json.load(f)
            return PintEconomy.model_validate(raw_data)
    except json.JSONDecodeError:
        print("Error: Malformed JSON in data file.")
        return PintEconomy()

def save_data(data: PintEconomy):
    """Save the PintEconomy data to a JSON file."""
    with open(config.DATA_FILE, "w") as f:
        json.dump(data.model_dump(), f, indent=2)