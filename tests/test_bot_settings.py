import pytest
from tests.conftest import DummyInteraction, DummyUser

class TestSettingsCommand:
    @pytest.mark.asyncio
    async def test_settings_command(self, bot):
        interaction = DummyInteraction(DummyUser(1), bot)
        await bot.tree.commands['settings'](interaction)
        calls = interaction.send_one_column_table_message_calls
        assert len(calls) == 1
        bot_cfg = calls[0]['kwargs']['data']
        assert any(item['Setting'] == 'Currency Name' for item in bot_cfg)