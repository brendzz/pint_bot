"""Optional audit log for all transactions.

When the ``AUDIT_LOG_WEBHOOK_URL`` environment variable is set to a
Discord channel webhook URL, every transaction created through the API
(owe, settle, auto-reverse) is posted to that webhook — including
transactions that did not go through the Discord bot (curl, scripts, ...).

Disabled by default. Audit delivery failures are logged and never affect
the transaction that triggered them.
"""
import logging
import os

import httpx

logger = logging.getLogger(__name__)

_WEBHOOK_TIMEOUT = 5
_BOT_USERNAME = "Pint Economy (audit log)"

_EMOJI = {"owe": "💸", "settle": "✅"}


def audit_log_enabled() -> bool:
    """Return True if an audit webhook URL is configured."""
    return bool(os.environ.get("AUDIT_LOG_WEBHOOK_URL", "").strip())


def format_transaction(entry) -> str:
    """Format a TransactionEntry as an audit message."""
    emoji = _EMOJI.get(entry.type, "📝")
    lines = [
        f"{emoji} **{entry.type.upper()}**  {entry.debtor} → {entry.creditor}",
        f"Amount: `{entry.amount}`",
    ]
    if entry.reason:
        lines.append(f"Reason: {entry.reason}")
    lines.append(f"At: {entry.timestamp}")
    return "\n".join(lines)


async def record_transaction(entry) -> None:
    """Post a transaction to the audit webhook. Never raises."""
    if not audit_log_enabled():
        return
    url = os.environ["AUDIT_LOG_WEBHOOK_URL"].strip()
    try:
        await _post_webhook(url, format_transaction(entry))
    except Exception as exc:
        # Audit must never break the economy: log loudly, carry on.
        logger.error("Failed to post transaction to audit log: %s", exc)


async def _post_webhook(url: str, content: str) -> None:
    payload = {
        "username": _BOT_USERNAME,
        "content": content,
        # Never ping anyone from user-supplied reasons (@everyone etc.)
        "allowed_mentions": {"parse": []},
    }
    async with httpx.AsyncClient(timeout=_WEBHOOK_TIMEOUT) as client:
        response = await client.post(url, json=payload)
        response.raise_for_status()
