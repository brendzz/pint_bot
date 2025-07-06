import pytest

from tests.conftest import DummyInteraction, DummyUser

class TestOweCommand:
    @pytest.mark.parametrize(
        "target_attr, error_code", [
            ("user", "CANNOT_OWE_SELF"),
            ("client", "CANNOT_OWE_BOT"),
        ],
        ids=["cant_owe_self", "cant_owe_bot"]
    )
    @pytest.mark.asyncio
    async def test_owe_errors(self, bot, target_attr, error_code):
        interaction = DummyInteraction(DummyUser(1), bot)
        parts = target_attr.split(".")
        target = interaction
        for attr in parts:
            target = getattr(target, attr)
        await bot.tree.commands['owe'](interaction, target, '1')
        assert interaction.error is not None
        assert interaction.error['kwargs']['error_code'] == error_code

    @pytest.mark.asyncio
    async def test_owe_success_and_defer(self, bot, shared):
        interaction = DummyInteraction(DummyUser(1), bot)
        target = DummyUser(2)
        await bot.tree.commands['owe'](interaction, target, '3', reason='Test')
        assert interaction.response.deferred
        assert shared.fake_api.calls['add_debt'] == {
            'debtor': 1, 'creditor': 2, 'amount': '3', 'reason': 'Test'
        }
        calls = interaction.send_success_message_calls
        assert calls
        kwargs = calls[0]['kwargs']
        assert '3' in kwargs['description']

class TestSettleCommand:
    @pytest.mark.parametrize(
        "target_attr, error_code", [
            ("user", "CANNOT_SETTLE_SELF"),
            ("client.user", "CANNOT_SETTLE_BOT"),
        ],
        ids=["cant_settle_self", "cant_settle_bot"]
    )
    @pytest.mark.asyncio
    async def test_settle_errors(self, bot, target_attr, error_code):
        interaction = DummyInteraction(DummyUser(1), bot)
        target = getattr(interaction, target_attr.split(".")[0])
        for attr in target_attr.split(".")[1:]:
            target = getattr(target, attr)
        await bot.tree.commands['settle'](interaction, target, '1')
        assert interaction.error is not None
        assert interaction.error['kwargs']['error_code'] == error_code

    @pytest.mark.asyncio
    async def test_settle_success_and_defer(self, bot, shared):
        interaction = DummyInteraction(DummyUser(1), bot)
        target = DummyUser(2)
        await bot.tree.commands['settle'](interaction, target, '5', 'Test')
        assert interaction.response.deferred
        assert shared.fake_api.calls['settle_debt'] == {
            'debtor': 1, 'creditor': 2, 'amount': '5', 'reason': 'Test'
        }
        calls = interaction.send_success_message_calls
        assert calls
        assert 'Settled 5 testcoins with <@2>' in calls[0]['kwargs']['description']