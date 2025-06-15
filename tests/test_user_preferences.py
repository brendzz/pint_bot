import pytest
from tests.conftest import DummyInteraction, DummyUser

class TestSetUnicodePreferenceCommand:
    @pytest.mark.parametrize("pref", [True, False])
    @pytest.mark.asyncio
    async def test_set_unicode_preference(self, bot, pref, shared):
        interaction = DummyInteraction(DummyUser(1), bot)
        await bot.tree.commands['set_unicode_preference'](interaction, pref)
        assert shared.fake_api.calls['set_unicode_preference'] == {'user_id': "1", 'use_unicode': pref}
        calls = interaction.send_success_message_calls
        assert calls
        assert calls[0]['kwargs']['title'] == 'Preference Updated'