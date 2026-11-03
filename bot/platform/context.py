"""Platform-independent types passed to command handlers.

A ``CommandContext`` carries everything a handler is allowed to know
about the invoking user and the chat it was invoked in. Handlers must
not import or reference platform-specific classes (``discord.Interaction``,
``telegram.Update``, ...) — everything they need goes through this
protocol, plus the ``Messenger`` protocol for sending replies.
"""
from dataclasses import dataclass
from typing import Any, Protocol, runtime_checkable


@dataclass(frozen=True)
class PlatformUser:
    """A user on any chat platform.

    Attributes:
        id: The platform user ID rendered as a string (Discord snowflakes,
            Telegram user IDs, ...). Always keep it a string.
        display_name: Human-readable name to show in messages.
        mention: Platform-native mention string for pinging the user.
    """

    id: str
    display_name: str
    mention: str


@runtime_checkable
class CommandContext(Protocol):
    """Everything a command handler needs from the chat platform."""

    # The invoking user
    user_id: str
    user_display_name: str
    user_mention: str

    # The platform's own bot/app user ID, as a string. Handlers use this
    # to reject interactions "with the bot itself".
    bot_user_id: str

    # The raw platform object (discord.Interaction, telegram.Update, ...).
    # Exists for escape hatches; handlers should prefer the other members.
    raw: Any

    # How replies are sent on this platform.
    messenger: "Messenger"  # noqa: F821 - imported from bot.platform for typing

    async def defer(self) -> None:
        """Acknowledge the interaction early (long-running API calls, ...)."""
        ...

    async def display_name(self, user_id: str, *, force_refresh: bool = False) -> str:
        """Resolve any user's display name (cached by the adapter)."""
        ...
