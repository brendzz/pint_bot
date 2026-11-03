"""Tests for the SQLite persistence layer."""
import json
from datetime import datetime, timezone
from fractions import Fraction

import pytest

from api.data_manager import SQLiteDataManager
from api.migrate_json_to_sqlite import migrate
from models import (
    DebtEntry,
    DebtsData,
    PreferencesData,
    TransactionEntry,
    UserDebts,
    UserPreferences,
)


@pytest.fixture
def manager(tmp_path):
    """Return a data manager backed by a temporary SQLite database."""
    return SQLiteDataManager(tmp_path / "pint_bot.db")


def make_debt(amount, reason="", timestamp="01-01-2025"):
    """Create a debt entry for tests."""
    return DebtEntry(amount=Fraction(amount), reason=reason, timestamp=timestamp)


def make_transaction(
    transaction_type,
    debtor,
    creditor,
    amount,
    timestamp,
    reason="",
):
    """Create a transaction entry for tests."""
    return TransactionEntry(
        type=transaction_type,
        debtor=debtor,
        creditor=creditor,
        amount=Fraction(amount),
        reason=reason,
        timestamp=timestamp,
    )


def test_in_memory_database_is_supported():
    manager = SQLiteDataManager(":memory:")
    manager.add_debt("alice", "bob", make_debt("1"))

    assert manager.load_debts().debtors["alice"].creditors["bob"][0].amount == Fraction(1)


def test_add_and_load_debts(manager):
    manager.add_debt("alice", "bob", make_debt("7/3", reason="first"))
    manager.add_debt("alice", "bob", make_debt("1/2", reason="second"))
    manager.add_debt("bob", "charlie", make_debt("2", reason="third"))

    data = manager.load_debts()

    assert set(data.debtors) == {"alice", "bob"}
    alice_debts = data.debtors["alice"].creditors["bob"]
    assert [entry.amount for entry in alice_debts] == [
        Fraction(7, 3),
        Fraction(1, 2),
    ]
    assert [entry.reason for entry in alice_debts] == ["first", "second"]
    assert data.debtors["bob"].creditors["charlie"][0].amount == Fraction(2)


def test_replace_debts(manager):
    manager.add_debt("alice", "bob", make_debt("1"))

    manager.replace_debts(
        DebtsData(
            debtors={
                "charlie": UserDebts(
                    creditors={"dave": [make_debt("3", reason="replacement")]}
                )
            }
        )
    )

    data = manager.load_debts()
    assert set(data.debtors) == {"charlie"}
    assert data.debtors["charlie"].creditors["dave"][0].amount == Fraction(3)


def test_settle_debt_uses_fifo_and_updates_the_database(manager):
    manager.add_debt("alice", "bob", make_debt("5", reason="oldest"))
    manager.add_debt("alice", "bob", make_debt("3", reason="newest"))

    result = manager.settle_debt("alice", "bob", Fraction(6))

    assert result is not None
    assert result.settled_amount == Fraction(6)
    assert result.remaining_amount == Fraction(2)

    remaining = manager.load_debts().debtors["alice"].creditors["bob"]
    assert len(remaining) == 1
    assert remaining[0].amount == Fraction(2)
    assert remaining[0].reason == "newest"
    assert remaining[0].timestamp == "01-01-2025"


def test_settle_debt_removes_fully_settled_entries(manager):
    manager.add_debt("alice", "bob", make_debt("4"))

    result = manager.settle_debt("alice", "bob", Fraction(4))

    assert result is not None
    assert result.settled_amount == Fraction(4)
    assert result.remaining_amount == Fraction(0)
    assert manager.load_debts().debtors == {}
    assert manager.settle_debt("alice", "bob", Fraction(1)) is None


def test_transactions_can_be_filtered(manager):
    manager.append_transaction(
        make_transaction("owe", "alice", "bob", "3/2", "2025-01-15T12:00:00Z")
    )
    manager.append_transaction(
        make_transaction("settle", "bob", "alice", "1", "2025-02-15T12:00:00Z")
    )
    manager.append_transaction(
        make_transaction("owe", "bob", "charlie", "2", "2025-03-15T12:00:00Z")
    )

    january = manager.get_transactions(
        start=datetime(2025, 1, 1, tzinfo=timezone.utc),
        end=datetime(2025, 1, 31, 23, 59, 59, tzinfo=timezone.utc),
    )
    assert len(january) == 1
    assert january[0].amount == Fraction(3, 2)

    alice_transactions = manager.get_transactions(user_id="alice")
    assert len(alice_transactions) == 2

    settlements = manager.get_transactions(transaction_type="settle")
    assert len(settlements) == 1
    assert settlements[0].debtor == "bob"
    assert manager.load_transactions().transactions == manager.get_transactions()


def test_unicode_preferences_can_be_created_and_updated(manager):
    assert manager.get_unicode_preference("alice") is False

    manager.set_unicode_preference("alice", True)
    assert manager.get_unicode_preference("alice") is True

    manager.set_unicode_preference("alice", False)
    assert manager.get_unicode_preference("alice") is False

    manager.replace_preferences(
        PreferencesData(users={"bob": UserPreferences(use_unicode=True)})
    )
    assert manager.load_preferences().users["bob"].use_unicode is True
    assert manager.get_unicode_preference("alice") is False


def test_legacy_json_can_be_migrated_once(tmp_path):
    data_directory = tmp_path / "data"
    data_directory.mkdir()
    database_file = tmp_path / "pint_bot.db"

    (data_directory / "debts.json").write_text(
        json.dumps(
            {
                "debtors": {
                    "alice": {
                        "creditors": {
                            "bob": [
                                {
                                    "amount": "3/2",
                                    "reason": "pint",
                                    "timestamp": "01-01-2025",
                                }
                            ]
                        }
                    }
                }
            }
        )
    )
    (data_directory / "transactions.json").write_text(
        json.dumps(
            {
                "transactions": [
                    {
                        "type": "owe",
                        "debtor": "alice",
                        "creditor": "bob",
                        "amount": "3/2",
                        "reason": "pint",
                        "timestamp": "2025-01-01T00:00:00Z",
                    }
                ]
            }
        )
    )
    (data_directory / "preferences.json").write_text(
        json.dumps({"users": {"alice": {"use_unicode": True}}})
    )

    counts = migrate(data_directory, database_file)

    assert counts == {"debts": 1, "transactions": 1, "preferences": 1}
    manager = SQLiteDataManager(database_file)
    assert manager.load_debts().debtors["alice"].creditors["bob"][0].amount == Fraction(
        3, 2
    )
    assert len(manager.load_transactions().transactions) == 1
    assert manager.get_unicode_preference("alice") is True

    with pytest.raises(RuntimeError, match="non-empty database"):
        migrate(data_directory, database_file)
