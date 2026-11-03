"""Protocol for sending command responses on any platform.

Semantic message levels (info/success/error) map to each platform's
idioms — colour-coded embeds on Discord, formatted text on Telegram,
etc. Handlers never construct platform-specific payloads themselves;
they describe *what* to say and the platform decides *how*.
"""
from typing import Any, Protocol, Sequence, runtime_checkable


@runtime_checkable
class Messenger(Protocol):
    """Sends command responses on behalf of handlers.

    Implementations receive the originating ``CommandContext`` (via
    ``ctx``) so they can reply in-place (e.g. Discord follow-ups,
    Telegram replies).
    """

    async def info(self, ctx: Any, *, title: str, description: str) -> None:
        """Send a neutral informational message."""
        ...

    async def success(self, ctx: Any, *, title: str, description: str) -> None:
        """Send a positive/success message."""
        ...

    async def error(self, ctx: Any, *, title: str, description: str) -> None:
        """Send an error message."""
        ...

    async def one_column_table(
        self,
        ctx: Any,
        *,
        title: str,
        description: str,
        data: Sequence[dict],
        table_format: bool,
    ) -> None:
        """Send a name/value table (used by e.g. the settings command).

        ``data`` rows are dicts with ``Setting`` and ``Value`` keys.
        ``table_format`` selects a compact two-column layout where the
        platform supports it.
        """
        ...

    async def two_column_table(
        self,
        ctx: Any,
        *,
        title: str,
        description: str,
        data: Sequence[dict],
        table_format: bool,
    ) -> None:
        """Send a three-column table (name, owes, is owed).

        ``data`` rows are dicts with ``name``, ``Owes`` and ``Is Owed`` keys.
        """
        ...
