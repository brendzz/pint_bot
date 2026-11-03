"""One-off migration from the legacy JSON files to the SQLite database.

Run from the repository root:

    python -m api.migrate_json_to_sqlite
"""
from __future__ import annotations

import json
from pathlib import Path

import api.config as config
from api.data_manager import SQLiteDataManager
from models import DebtsData, PreferencesData, TransactionsData

DATA_DIRECTORY = Path(__file__).resolve().parent / "data"


def _load_json(file_path: Path, model, fallback):
    """Load a legacy JSON file, returning an empty model when it is absent."""
    if not file_path.exists():
        return model(**fallback)
    return model(**json.loads(file_path.read_text()))


def migrate(
    data_directory: Path = DATA_DIRECTORY,
    database_file: Path = config.DATABASE_FILE,
) -> dict[str, int]:
    """Import legacy JSON data into an empty SQLite database."""
    debts = _load_json(data_directory / "debts.json", DebtsData, {"debtors": {}})
    transactions = _load_json(
        data_directory / "transactions.json",
        TransactionsData,
        {"transactions": []},
    )
    preferences = _load_json(
        data_directory / "preferences.json",
        PreferencesData,
        {"users": {}},
    )

    manager = SQLiteDataManager(database_file)
    if (
        manager.load_debts().debtors
        or manager.load_transactions().transactions
        or manager.load_preferences().users
    ):
        raise RuntimeError(
            f"Refusing to migrate into non-empty database: {database_file}"
        )

    counts = {"debts": 0, "transactions": 0, "preferences": 0}

    for debtor_id, debtor in debts.debtors.items():
        for creditor_id, entries in debtor.creditors.items():
            for entry in entries:
                manager.add_debt(debtor_id, creditor_id, entry)
                counts["debts"] += 1

    for entry in transactions.transactions:
        manager.append_transaction(entry)
        counts["transactions"] += 1

    for user_id, user_preferences in preferences.users.items():
        manager.set_unicode_preference(user_id, user_preferences.use_unicode)
        counts["preferences"] += 1

    return counts


def main() -> None:
    """Run the migration and print a summary."""
    counts = migrate()
    print(
        "Migration complete: "
        f"{counts['debts']} debts, "
        f"{counts['transactions']} transactions, "
        f"{counts['preferences']} preferences imported into {config.DATABASE_FILE}."
    )


if __name__ == "__main__":
    main()
