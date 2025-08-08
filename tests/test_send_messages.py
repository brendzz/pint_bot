import pytest
from unittest.mock import AsyncMock, MagicMock
import discord

@pytest.mark.asyncio
async def test_send_message_splits_long_description(monkeypatch):
    # Arrange
    from bot.utilities import message_processor
    limit = 100  # Use a small limit for testing
    monkeypatch.setattr(message_processor.config, "DISCORD_EMBED_DESCRIPTION_LIMIT", limit)
    long_text = "A" * (limit * 2 + 10)  # Will require 3 chunks

    # Mock interaction and followup.send
    interaction = MagicMock()
    interaction.followup.send = AsyncMock()

    # Act
    await message_processor.send_message(
        interaction,
        title="Test Title",
        description=long_text,
        color=discord.Color.blue()
    )

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