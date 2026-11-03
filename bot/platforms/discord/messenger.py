"""Discord implementation of the Messenger protocol.

Uses colour-coded embeds (blue/green/red) and handles Discord's
embed limits: titles are truncated to DISCORD_EMBED_TITLE_LIMIT,
descriptions are split at newline boundaries into chunks of
DISCORD_EMBED_DESCRIPTION_LIMIT.
"""
import discord

import bot.config as config
from bot.platform.context import CommandContext
from bot.utilities.message_processor import split_text_into_chunks


def truncate_title(title: str) -> str:
    """Truncate an embed title to Discord's character limit (with an ellipsis)."""
    limit = config.DISCORD_EMBED_TITLE_LIMIT
    if len(title) <= limit:
        return title
    return title[: limit - 1] + "…"


class DiscordMessenger:
    """Sends messages as Discord embeds."""

    async def info(self, ctx: CommandContext, *, title: str, description: str) -> None:
        await self._send(ctx, title, description, discord.Color.blue())

    async def success(self, ctx: CommandContext, *, title: str, description: str) -> None:
        await self._send(ctx, title, description, discord.Color.green())

    async def error(self, ctx: CommandContext, *, title: str, description: str) -> None:
        await self._send(ctx, title, description, discord.Color.red())

    async def one_column_table(
        self,
        ctx: CommandContext,
        *,
        title: str,
        description: str,
        data: list[dict],
        table_format: bool,
    ) -> None:
        """Sends a one-column settings table (Setting -> Value)."""
        chunks = _chunk(data)
        for i, chunk in enumerate(chunks):
            embed = discord.Embed(
                title=_page_title(title, i, len(chunks)),
                description=description if i == 0 else None,
                color=discord.Color.yellow(),
            )
            if table_format:
                embed.add_field(name="Setting", value="\n".join(row["Setting"] for row in chunk), inline=True)
                embed.add_field(name="Value", value="\n".join(str(row["Value"]) for row in chunk), inline=True)
            else:
                for row in chunk:
                    embed.add_field(name=row["Setting"], value=f"{row['Value']}", inline=False)
            await _send_embed(ctx, embed)

    async def two_column_table(
        self,
        ctx: CommandContext,
        *,
        title: str,
        description: str,
        data: list[dict],
        table_format: bool,
    ) -> None:
        """Sends a two-column debts table (name, Owes, Is Owed)."""
        chunks = _chunk(data)
        for i, chunk in enumerate(chunks):
            embed = discord.Embed(
                title=_page_title(title, i, len(chunks)),
                description=description if i == 0 else None,
                color=discord.Color.yellow(),
            )
            if table_format:
                embed.add_field(name="Name", value="\n".join(row["name"] for row in chunk), inline=True)
                embed.add_field(name="Owes", value="\n".join(str(row["Owes"]) for row in chunk), inline=True)
                embed.add_field(name="Is Owed", value="\n".join(str(row["Is Owed"]) for row in chunk), inline=True)
            else:
                for row in chunk:
                    user_data = f"**Owes:** {row['Owes']}\n**Is Owed:** {row['Is Owed']}"
                    embed.add_field(name=row["name"], value=user_data, inline=False)
            await _send_embed(ctx, embed)

    async def _send(self, ctx: CommandContext, title: str, description: str, color: discord.Color) -> None:
        title = truncate_title(title)
        interaction = ctx.raw
        if len(description) <= config.DISCORD_EMBED_DESCRIPTION_LIMIT:
            embed = discord.Embed(title=title, description=description, color=color)
            await _send_embed(ctx, embed)
            return
        chunks = split_text_into_chunks(description, config.DISCORD_EMBED_DESCRIPTION_LIMIT)
        for i, chunk in enumerate(chunks):
            embed = discord.Embed(title=title if i == 0 else None, description=chunk, color=color)
            await _send_embed(ctx, embed)


_EMBED_FIELD_CHUNK = 25  # Discord's limit for embed fields


def _chunk(data: list[dict]) -> list[list[dict]]:
    return [data[i:i + _EMBED_FIELD_CHUNK] for i in range(0, len(data), _EMBED_FIELD_CHUNK)]


def _page_title(title: str, page: int, total_pages: int) -> str:
    return f"{title} (Page {page + 1}/{total_pages})" if total_pages > 1 else title


async def _send_embed(ctx: CommandContext, embed: discord.Embed) -> None:
    interaction = ctx.raw
    if not interaction.response.is_done():
        await interaction.response.send_message(embed=embed)
    else:
        await interaction.followup.send(embed=embed)
