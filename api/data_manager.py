"""Module for handling data loading and saving.

Data is stored as JSON files. All writes are atomic (temporary file +
``os.replace``) and the previous contents of a file are kept as a
``.bak`` backup. If the main file is missing or corrupted, the backup
is used instead. If neither can be parsed a :class:`DataStoreError`
is raised so the API can return a controlled error response instead of
a stack trace.
"""
import json
import logging
import os
import shutil
from pathlib import Path

from models import (
    DebtsData,
    TransactionsData,
    TransactionEntry,
    PreferencesData,
)

logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent
DATA_DIRECTORY = BASE_DIR / "data"
DEBTS_FILE = DATA_DIRECTORY / "debts.json"
TRANSACTIONS_FILE = DATA_DIRECTORY / "transactions.json"
PREFERENCES_FILE = DATA_DIRECTORY / "preferences.json"


class DataStoreError(Exception):
    """Raised when a data file cannot be read or written."""


def _parse(raw: str, file_path: Path, model, fallback):
    try:
        return model(**json.loads(raw))
    except Exception as exc:
        raise DataStoreError(f"Could not parse data file {file_path}") from exc


def load_data(file_path: Path, model, fallback):
    """Generic loader for JSON files with backup recovery."""
    backup_path = file_path.with_suffix(file_path.suffix + ".bak")

    if file_path.exists():
        try:
            return _parse(file_path.read_text(), file_path, model, fallback)
        except DataStoreError:
            logger.error("Data file %s is corrupt; attempting to restore backup %s", file_path, backup_path)
            if backup_path.exists():
                try:
                    restored = _parse(backup_path.read_text(), backup_path, model, fallback)
                    shutil.copy2(backup_path, file_path)
                    logger.warning("Restored %s from backup", file_path)
                    return restored
                except DataStoreError:
                    logger.error("Backup %s is also unusable", backup_path)
            raise DataStoreError(f"Data file {file_path} is corrupt and no usable backup exists")

    if backup_path.exists():
        try:
            restored = _parse(backup_path.read_text(), backup_path, model, fallback)
            shutil.copy2(backup_path, file_path)
            logger.warning("Data file %s was missing; restored from backup", file_path)
            return restored
        except DataStoreError:
            logger.error("Backup %s is unusable", backup_path)

    return model(**fallback)


def save_data(file_path: Path, data):
    """Generic saver for JSON files.

    Writes are atomic: the new contents go to a temporary file which is
    then renamed over the target. The previous contents are preserved
    as a ``.bak`` file first.
    """
    file_path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = file_path.with_suffix(file_path.suffix + ".tmp")
    backup_path = file_path.with_suffix(file_path.suffix + ".bak")

    if file_path.exists():
        try:
            shutil.copy2(file_path, backup_path)
        except OSError as exc:
            # A failed backup must not prevent saving, but it must be loud.
            logger.error("Could not create backup %s: %s", backup_path, exc)

    try:
        tmp_path.write_text(json.dumps(data.model_dump(), indent=2))
        os.replace(tmp_path, file_path)
    except OSError as exc:
        try:
            tmp_path.unlink(missing_ok=True)
        except OSError:
            pass
        raise DataStoreError(f"Could not write data file {file_path}") from exc

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
