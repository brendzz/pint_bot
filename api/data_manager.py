"""Persistence layer for debts, transactions, and user preferences.

The API talks to the :class:`DataManager` interface rather than constructing
SQL directly.  ``SQLiteDataManager`` is the local SQLite implementation used by
the application, so another storage backend can be added without changing the
endpoints.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime, timezone
from fractions import Fraction
from functools import lru_cache
from pathlib import Path

import api.config as config
from api.database import SQLiteDatabase
from api.utilities.debt_helpers import settle_debts_between_users
from models import (
    DebtEntry,
    DebtsData,
    PreferencesData,
    TransactionEntry,
    TransactionsData,
    UserDebts,
    UserPreferences,
)


@dataclass(frozen=True)
class SettlementResult:
    """The result of settling debts between a pair of users."""

    settled_amount: Fraction
    remaining_amount: Fraction


def _fraction_columns(value: Fraction) -> tuple[int, int]:
    """Return the exact numerator and denominator stored in SQLite."""
    fraction = Fraction(value)
    return fraction.numerator, fraction.denominator


def _normalize_timestamp(timestamp: str) -> str:
    """Store transaction timestamps in a consistent UTC ISO-8601 format."""
    try:
        parsed = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
    except (AttributeError, ValueError):
        return timestamp

    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _query_timestamp(value: datetime) -> str:
    """Format a datetime for comparisons against stored timestamps."""
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


class DataManager(ABC):
    """Abstract storage interface used by the API."""

    @abstractmethod
    def load_debts(self) -> DebtsData:
        """Load all outstanding debts."""

    @abstractmethod
    def add_debt(self, debtor_id: str, creditor_id: str, entry: DebtEntry) -> None:
        """Add a single debt entry."""

    @abstractmethod
    def replace_debts(self, data: DebtsData) -> None:
        """Replace all stored debts with the supplied snapshot."""

    @abstractmethod
    def settle_debt(
        self,
        debtor_id: str,
        creditor_id: str,
        amount: Fraction,
    ) -> SettlementResult | None:
        """Settle debts between two users in FIFO order.

        Returns ``None`` when there are no debts between the pair.
        """

    @abstractmethod
    def get_transactions(
        self,
        start: datetime | None = None,
        end: datetime | None = None,
        user_id: str | None = None,
        transaction_type: str | None = None,
    ) -> list[TransactionEntry]:
        """Load transactions, optionally filtered by date, user, and type."""

    @abstractmethod
    def append_transaction(self, entry: TransactionEntry) -> None:
        """Append a single transaction."""

    @abstractmethod
    def load_preferences(self) -> PreferencesData:
        """Load all user preferences."""

    @abstractmethod
    def replace_preferences(self, data: PreferencesData) -> None:
        """Replace all stored user preferences with the supplied snapshot."""

    @abstractmethod
    def get_unicode_preference(self, user_id: str) -> bool:
        """Return a user's Unicode preference."""

    @abstractmethod
    def set_unicode_preference(self, user_id: str, use_unicode: bool) -> None:
        """Create or update a user's Unicode preference."""


class SQLiteDataManager(DataManager):
    """SQLite implementation of the API persistence interface."""

    def __init__(self, database: SQLiteDatabase | str | Path):
        self.database = (
            database if isinstance(database, SQLiteDatabase) else SQLiteDatabase(database)
        )

    def load_debts(self) -> DebtsData:
        with self.database.connect() as connection:
            rows = connection.execute(
                """
                SELECT debtor_id, creditor_id, amount_numerator,
                       amount_denominator, reason, timestamp
                FROM debts
                ORDER BY id
                """
            ).fetchall()

        debtors: dict[str, UserDebts] = {}
        for row in rows:
            debtor = debtors.setdefault(row["debtor_id"], UserDebts())
            debtor.creditors.setdefault(row["creditor_id"], []).append(
                DebtEntry(
                    amount=Fraction(
                        row["amount_numerator"],
                        row["amount_denominator"],
                    ),
                    reason=row["reason"],
                    timestamp=row["timestamp"],
                )
            )

        return DebtsData(debtors=debtors)

    def add_debt(self, debtor_id: str, creditor_id: str, entry: DebtEntry) -> None:
        numerator, denominator = _fraction_columns(entry.amount)
        with self.database.connect() as connection:
            connection.execute(
                """
                INSERT INTO debts (
                    debtor_id, creditor_id, amount_numerator,
                    amount_denominator, reason, timestamp
                ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    debtor_id,
                    creditor_id,
                    numerator,
                    denominator,
                    entry.reason,
                    entry.timestamp,
                ),
            )

    def replace_debts(self, data: DebtsData) -> None:
        rows = [
            (
                debtor_id,
                creditor_id,
                *_fraction_columns(entry.amount),
                entry.reason,
                entry.timestamp,
            )
            for debtor_id, debtor in data.debtors.items()
            for creditor_id, entries in debtor.creditors.items()
            for entry in entries
        ]

        with self.database.connect() as connection:
            connection.execute("DELETE FROM debts")
            connection.executemany(
                """
                INSERT INTO debts (
                    debtor_id, creditor_id, amount_numerator,
                    amount_denominator, reason, timestamp
                ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                rows,
            )

    def settle_debt(
        self,
        debtor_id: str,
        creditor_id: str,
        amount: Fraction,
    ) -> SettlementResult | None:
        with self.database.connect() as connection:
            rows = connection.execute(
                """
                SELECT id, amount_numerator, amount_denominator, reason, timestamp
                FROM debts
                WHERE debtor_id = ? AND creditor_id = ?
                ORDER BY id
                """,
                (debtor_id, creditor_id),
            ).fetchall()

            if not rows:
                return None

            entries = [
                DebtEntry(
                    amount=Fraction(
                        row["amount_numerator"],
                        row["amount_denominator"],
                    ),
                    reason=row["reason"],
                    timestamp=row["timestamp"],
                )
                for row in rows
            ]
            updated_entries, settled_amount = settle_debts_between_users(
                entries,
                amount,
            )

            removed_count = len(rows) - len(updated_entries)
            if removed_count:
                connection.executemany(
                    "DELETE FROM debts WHERE id = ?",
                    [(row["id"],) for row in rows[:removed_count]],
                )

            for row, entry in zip(rows[removed_count:], updated_entries):
                numerator, denominator = _fraction_columns(entry.amount)
                connection.execute(
                    """
                    UPDATE debts
                    SET amount_numerator = ?, amount_denominator = ?
                    WHERE id = ?
                    """,
                    (numerator, denominator, row["id"]),
                )

        remaining_amount = sum(
            (entry.amount for entry in updated_entries),
            Fraction(0),
        )
        return SettlementResult(
            settled_amount=settled_amount,
            remaining_amount=remaining_amount,
        )

    def get_transactions(
        self,
        start: datetime | None = None,
        end: datetime | None = None,
        user_id: str | None = None,
        transaction_type: str | None = None,
    ) -> list[TransactionEntry]:
        clauses: list[str] = []
        parameters: list[str] = []

        if start is not None:
            clauses.append("timestamp >= ?")
            parameters.append(_query_timestamp(start))
        if end is not None:
            clauses.append("timestamp <= ?")
            parameters.append(_query_timestamp(end))
        if user_id:
            clauses.append("(debtor_id = ? OR creditor_id = ?)")
            parameters.extend((user_id, user_id))
        if transaction_type:
            clauses.append("type = ?")
            parameters.append(transaction_type)

        query = """
            SELECT type, debtor_id, creditor_id, amount_numerator,
                   amount_denominator, reason, timestamp
            FROM transactions
        """
        if clauses:
            query += " WHERE " + " AND ".join(clauses)
        query += " ORDER BY id"

        with self.database.connect() as connection:
            rows = connection.execute(query, parameters).fetchall()

        return [
            TransactionEntry(
                type=row["type"],
                debtor=row["debtor_id"],
                creditor=row["creditor_id"],
                amount=Fraction(
                    row["amount_numerator"],
                    row["amount_denominator"],
                ),
                reason=row["reason"],
                timestamp=row["timestamp"],
            )
            for row in rows
        ]

    def load_transactions(self) -> TransactionsData:
        return TransactionsData(transactions=self.get_transactions())

    def append_transaction(self, entry: TransactionEntry) -> None:
        numerator, denominator = _fraction_columns(entry.amount)
        with self.database.connect() as connection:
            connection.execute(
                """
                INSERT INTO transactions (
                    type, debtor_id, creditor_id, amount_numerator,
                    amount_denominator, reason, timestamp
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    entry.type,
                    entry.debtor,
                    entry.creditor,
                    numerator,
                    denominator,
                    entry.reason,
                    _normalize_timestamp(entry.timestamp),
                ),
            )

    def load_preferences(self) -> PreferencesData:
        with self.database.connect() as connection:
            rows = connection.execute(
                "SELECT user_id, use_unicode FROM preferences ORDER BY user_id"
            ).fetchall()

        return PreferencesData(
            users={
                row["user_id"]: UserPreferences(use_unicode=bool(row["use_unicode"]))
                for row in rows
            }
        )

    def replace_preferences(self, data: PreferencesData) -> None:
        with self.database.connect() as connection:
            connection.execute("DELETE FROM preferences")
            connection.executemany(
                """
                INSERT INTO preferences (user_id, use_unicode)
                VALUES (?, ?)
                """,
                [
                    (user_id, int(preferences.use_unicode))
                    for user_id, preferences in data.users.items()
                ],
            )

    def get_unicode_preference(self, user_id: str) -> bool:
        with self.database.connect() as connection:
            row = connection.execute(
                "SELECT use_unicode FROM preferences WHERE user_id = ?",
                (user_id,),
            ).fetchone()

        return bool(row["use_unicode"]) if row else False

    def set_unicode_preference(self, user_id: str, use_unicode: bool) -> None:
        with self.database.connect() as connection:
            connection.execute(
                """
                INSERT INTO preferences (user_id, use_unicode)
                VALUES (?, ?)
                ON CONFLICT(user_id) DO UPDATE SET use_unicode = excluded.use_unicode
                """,
                (user_id, int(use_unicode)),
            )


@lru_cache(maxsize=1)
def get_data_manager() -> DataManager:
    """Return the application's configured data manager."""
    return SQLiteDataManager(config.DATABASE_FILE)


# Convenience functions keep the API endpoints and existing callers decoupled
# from the concrete storage implementation.
def load_debts() -> DebtsData:
    """Load all debts."""
    return get_data_manager().load_debts()


def save_debts(data: DebtsData) -> None:
    """Replace all debts with the supplied snapshot."""
    get_data_manager().replace_debts(data)


def add_debt(debtor_id: str, creditor_id: str, entry: DebtEntry) -> None:
    """Add a debt entry."""
    get_data_manager().add_debt(debtor_id, creditor_id, entry)


def settle_debt(
    debtor_id: str,
    creditor_id: str,
    amount: Fraction,
) -> SettlementResult | None:
    """Settle debts between two users."""
    return get_data_manager().settle_debt(debtor_id, creditor_id, amount)


def load_transactions() -> TransactionsData:
    """Load all transactions."""
    return get_data_manager().load_transactions()


def get_transactions(
    start: datetime | None = None,
    end: datetime | None = None,
    user_id: str | None = None,
    transaction_type: str | None = None,
) -> list[TransactionEntry]:
    """Load transactions with optional filters."""
    return get_data_manager().get_transactions(
        start=start,
        end=end,
        user_id=user_id,
        transaction_type=transaction_type,
    )


def append_transaction(entry: TransactionEntry) -> None:
    """Append a transaction."""
    get_data_manager().append_transaction(entry)


def load_preferences() -> PreferencesData:
    """Load all user preferences."""
    return get_data_manager().load_preferences()


def save_preferences(data: PreferencesData) -> None:
    """Replace all user preferences with the supplied snapshot."""
    get_data_manager().replace_preferences(data)


def get_unicode_preference(user_id: str) -> bool:
    """Load a user's Unicode preference."""
    return get_data_manager().get_unicode_preference(user_id)


def set_unicode_preference(user_id: str, use_unicode: bool) -> None:
    """Create or update a user's Unicode preference."""
    get_data_manager().set_unicode_preference(user_id, use_unicode)
