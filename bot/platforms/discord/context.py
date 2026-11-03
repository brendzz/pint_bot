"""Discord implementation of the CommandContext protocol."""
import discord

from bot.platform.context import PlatformUser
from bot.utilities.display_names import resolve_display_name


def platform_user_from_discord(user) -> PlatformUser:
    """Build a PlatformUser from a Discord user (or compatible test double)."""
    user_id = str(user.id)
    display_name = getattr(user, "display_name", None) or str(user_id)
    mention = getattr(user, "mention", None) or f"<@{user_id}>"
    return PlatformUser(id=user_id, display_name=display_name, mention=mention)


class DiscordCommandContext:
    """Adapts a discord.Interaction to the platform-agnostic CommandContext protocol."""

    def __init__(self, interaction: "discord.Interaction"):
        from bot.platforms.discord.messenger import DiscordMessenger

        self.interaction = interaction
        self.raw = interaction
        self.messenger = DiscordMessenger()

        invoking_user = interaction.user
        self.user_id = str(invoking_user.id)
        self.user_display_name = invoking_user.display_name
        self.user_mention = getattr(invoking_user, "mention", f"<@{invoking_user.id}>")
        self.bot_user_id = str(interaction.client.user.id)

    async def defer(self) -> None:
        await self.interaction.response.defer()

    async def display_name(self, user_id: str, *, force_refresh: bool = False) -> str:
        async def fetch(uid: str) -> str | None:
            try:
                user = await self.interaction.client.fetch_user(int(uid))
                return user.display_name
            except Exception:
                return None

        return await resolve_display_name(str(user_id), fetch, force_refresh=force_refresh)
