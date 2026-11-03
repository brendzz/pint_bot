import pytest
from unittest.mock import AsyncMock, MagicMock
import discord
from tests.conftest import REAL_DISCORD_MESSENGER

@pytest.fixture(autouse=True)
def restore_real_messenger(monkeypatch):
    # The test-suite's global fixture replaces DiscordMessenger with a
    # recording double; restore the real class for these tests.
    monkeypatch.setattr(
        "bot.platforms.discord.messenger.DiscordMessenger",
        REAL_DISCORD_MESSENGER,
    )

@pytest.mark.asyncio
async def test_send_message_splits_long_description(monkeypatch):
    # Arrange
    from bot.platforms.discord import messenger as discord_messenger
    limit = 100  # Use a small limit for testing
    monkeypatch.setattr(discord_messenger.config, "DISCORD_EMBED_DESCRIPTION_LIMIT", limit)
    long_text = "A" * (limit * 2 + 10)  # Will require 3 chunks

    # Mock the raw interaction and a context carrying it
    interaction = MagicMock()
    interaction.response.is_done.return_value = True
    interaction.followup.send = AsyncMock()
    ctx = MagicMock()
    ctx.raw = interaction

    messenger = discord_messenger.DiscordMessenger()

    # Act
    await messenger.info(ctx, title="Test Title", description=long_text)

    # Assert
    # Should send 3 embeds: 1 with title, 2 without
    assert interaction.followup.send.call_count == 3
    # First embed has title, others do not
    first_embed = interaction.followup.send.call_args_list[0][1]['embed']
    assert first_embed.title == "Test Title"
    for call in interaction.followup.send.call_args_list[1:]:
        embed = call[1]['embed']
        assert embed.title is None
    # All descriptions are within the limit
    for call in interaction.followup.send.call_args_list:
        embed = call[1]['embed']
        assert len(embed.description) <= limit


@pytest.mark.asyncio
async def test_title_longer_than_limit_is_truncated(monkeypatch):
    from bot.platforms.discord import messenger as discord_messenger
    monkeypatch.setattr(discord_messenger.config, "DISCORD_EMBED_TITLE_LIMIT", 10)

    interaction = MagicMock()
    interaction.response.is_done.return_value = False
    interaction.response.send_message = AsyncMock()
    ctx = MagicMock()
    ctx.raw = interaction

    messenger = discord_messenger.DiscordMessenger()
    await messenger.info(ctx, title="This title is far too long for the limit", description="hi")

    embed = interaction.response.send_message.call_args_list[0][1]['embed']
    assert len(embed.title) == 10
    assert embed.title.endswith("…")
