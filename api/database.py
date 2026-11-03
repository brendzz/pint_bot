"""SQLite connection management and schema definition."""
from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator
from uuid import uuid4

SCHEMA = """
CREATE TABLE IF NOT EXISTS debts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    debtor_id TEXT NOT NULL,
    creditor_id TEXT NOT NULL,
    amount_numerator INTEGER NOT NULL CHECK (amount_numerator > 0),
    amount_denominator INTEGER NOT NULL CHECK (amount_denominator > 0),
    reason TEXT NOT NULL DEFAULT '',
    timestamp TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_debts_debtor_creditor
    ON debts (debtor_id, creditor_id);

CREATE INDEX IF NOT EXISTS idx_debts_creditor
    ON debts (creditor_id);

CREATE TABLE IF NOT EXISTS transactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    type TEXT NOT NULL CHECK (type IN ('owe', 'settle')),
    debtor_id TEXT NOT NULL,
    creditor_id TEXT NOT NULL,
    amount_numerator INTEGER NOT NULL CHECK (amount_numerator > 0),
    amount_denominator INTEGER NOT NULL CHECK (amount_denominator > 0),
    reason TEXT NOT NULL DEFAULT '',
    timestamp TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_transactions_timestamp
    ON transactions (timestamp);

CREATE INDEX IF NOT EXISTS idx_transactions_debtor
    ON transactions (debtor_id);

CREATE INDEX IF NOT EXISTS idx_transactions_creditor
    ON transactions (creditor_id);

CREATE TABLE IF NOT EXISTS preferences (
    user_id TEXT PRIMARY KEY,
    use_unicode INTEGER NOT NULL DEFAULT 0 CHECK (use_unicode IN (0, 1))
);
"""


class SQLiteDatabase:
    """Manage connections to a local SQLite database."""

    def __init__(self, path: str | Path):
        self.path = str(path)
        self._memory_anchor: sqlite3.Connection | None = None
        if self.path == ":memory:":
            # Keep one connection open so the shared in-memory database survives
            # between the short-lived connections used for each operation.
            self._uri = f"file:pint_bot_{uuid4().hex}?mode=memory&cache=shared"
            self._memory_anchor = sqlite3.connect(self._uri, uri=True)
        else:
            self._uri = self.path
            Path(self.path).expanduser().parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    @contextmanager
    def connect(self) -> Iterator[sqlite3.Connection]:
        """Open a connection and commit or roll back the operation."""
        connection = sqlite3.connect(
            self._uri,
            timeout=30,
            uri=self._memory_anchor is not None,
        )
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute("PRAGMA busy_timeout = 30000")
        try:
            yield connection
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    def _initialize(self) -> None:
        """Create the database schema if it does not already exist."""
        with self.connect() as connection:
            connection.execute("PRAGMA journal_mode = WAL")
            connection.executescript(SCHEMA)
