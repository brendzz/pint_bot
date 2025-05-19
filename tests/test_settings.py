import pytest

from bot import api_client
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

class TestSetUnicodePreferenceCommand:
    @pytest.mark.parametrize("pref", [True, False])
    @pytest.mark.asyncio
    async def test_set_unicode_preference(self, bot, pref):
        interaction = DummyInteraction(DummyUser(1), bot)
        await bot.tree.commands['set_unicode_preference'](interaction, pref)
        assert api_client.calls['set_unicode_preference'] == {'user_id': "1", 'use_unicode': pref}
        calls = interaction.send_success_message_calls
        assert calls
        assert calls[0]['kwargs']['title'] == 'Preference Updated'