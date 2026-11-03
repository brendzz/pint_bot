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
class TestExcessReverseDisplay:
    @pytest.mark.asyncio
    async def test_settle_shows_reverse_line(self, bot, shared, monkeypatch):
        async def settle_with_reverse(payload):
            return {'settled_amount': '1', 'remaining_amount': '0', 'auto_reversed_amount': '2'}

        monkeypatch.setattr(shared.fake_api, 'settle_debt', settle_with_reverse)
        interaction = DummyInteraction(DummyUser(1), bot)
        await bot.tree.commands['settle'](interaction, DummyUser(2), '4')
        calls = interaction.send_success_message_calls
        assert calls
        assert any('now owes you' in c['kwargs']['description'] for c in calls)

    @pytest.mark.asyncio
    async def test_cashout_shows_reverse_line(self, bot, shared, monkeypatch):
        async def settle_with_reverse(payload):
            return {'settled_amount': '1', 'remaining_amount': '0', 'auto_reversed_amount': '2'}

        monkeypatch.setattr(shared.fake_api, 'settle_debt', settle_with_reverse)
        interaction = DummyInteraction(DummyUser(1), bot)
        await bot.tree.commands['cashout'](interaction, DummyUser(2), '4')
        calls = interaction.send_success_message_calls
        assert calls
        assert any('You now owe' in c['kwargs']['description'] for c in calls)

    @pytest.mark.asyncio
    async def test_settle_without_reverse_omits_reverse_line(self, bot, shared):
        interaction = DummyInteraction(DummyUser(1), bot)
        await bot.tree.commands['settle'](interaction, DummyUser(2), '4')
        calls = interaction.send_success_message_calls
        assert calls
        assert all('now owes you' not in c['kwargs']['description'] for c in calls)
        assert all('You now owe' not in c['kwargs']['description'] for c in calls)
