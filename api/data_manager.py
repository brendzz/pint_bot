"""Module for handling data loading and saving."""
import json
from pathlib import Path
from models import (
    DebtsData,
    TransactionsData,
    TransactionEntry,
    PreferencesData,
)

BASE_DIR = Path(__file__).resolve().parent
DATA_DIRECTORY = BASE_DIR / "data"
DEBTS_FILE = DATA_DIRECTORY / "debts.json"
TRANSACTIONS_FILE = DATA_DIRECTORY / "transactions.json"
PREFERENCES_FILE = DATA_DIRECTORY / "preferences.json"

def load_data(file_path: Path, model, fallback):
    """Generic loader for JSON files with fallback."""
    if not file_path.exists():
        return model(**fallback)
    return model(**json.loads(file_path.read_text()))

def save_data(file_path: Path, data):
    """Generic saver for JSON files."""
    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_path.write_text(json.dumps(data.model_dump(), indent=2))

# --- Debts ---
def load_debts() -> DebtsData:
    """Load debts data."""
    fallback = {"debtors": {}}
    return load_data(DEBTS_FILE, DebtsData, fallback)

def save_debts(data: DebtsData):
    """Save debts data."""
    save_data(DEBTS_FILE, data)

# --- Transactions ---
def load_transactions() -> TransactionsData:
    """Load transactions data."""
    fallback = {"transactions": []}
    return load_data(TRANSACTIONS_FILE, TransactionsData, fallback)

def append_transaction(entry: TransactionEntry):
    """Append a new transaction entry."""
    transactions_data = load_transactions()
    transactions_data.transactions.append(entry)
    save_data(TRANSACTIONS_FILE, transactions_data)

# --- Preferences ---
def load_preferences() -> PreferencesData:
    """Load user preferences data."""
    fallback = {"users": {}}
    return load_data(PREFERENCES_FILE, PreferencesData, fallback)

def save_preferences(data: PreferencesData):
    """Save user preferences data."""
    save_data(PREFERENCES_FILE, data)
