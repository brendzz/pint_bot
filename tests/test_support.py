from unittest.mock import patch
import pytest

from bot.register_commands import register_commands
from bot.command import Command
from tests.conftest import DummyInteraction, DummyUser

class TestHelpCommand:
    @pytest.mark.asyncio
    async def test_help_commands_section(self, bot):
        # Clear and register commands
        Command._registry.clear()
        Command(key="help", name="help", description="Show help", category="Support")
        Command(key="owe", name="owe", description="See what you owe", category="Core")
        Command(key="settle", name="settle", description="Settle up", category="Core")
        Command(key="gift", name="gift", description="Gift a debt", category="Fun")

        register_commands(bot)  # <-- This is crucial

        interaction = DummyInteraction(DummyUser(1), bot)
        cmd = bot.tree.commands["help"]
        await cmd(interaction)

        assert interaction.response.deferred
        msg = interaction.send_info_message_calls[0]['kwargs']['description']

        for category in ["Core", "Fun"]:
            assert f"**{category}:**" in msg
        for name, desc in [("owe", "See what you owe"), ("settle", "Settle up"), ("gift", "Gift a debt")]:
            assert f"**/{name}** — {desc}" in msg

    @pytest.mark.asyncio
    async def test_help_uses_section(self, bot):
        import bot.config as config
        interaction = DummyInteraction(DummyUser(1), bot)
        cmd = bot.tree.commands['help']
        await cmd(interaction)
        assert interaction.response.deferred
        calls = interaction.send_info_message_calls
        assert calls
        kwargs = calls[0]['kwargs']
        assert kwargs["title"] == f"{config.BOT_NAME} Help"

        # Check that reward items are listed
        for item in config.TRANSFERABLE_ITEMS:
            assert f"- {item}" in kwargs["description"]