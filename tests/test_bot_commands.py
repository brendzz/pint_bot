import pytest
import bot_commands as commands

# Dummy Discord objects for testing
class DummyUser:
    def __init__(self, id, display_name=None):
        self.id = id
        self.display_name = display_name or f'User{self.id}'
        self.mention = f'<@{self.id}>'

class DummyResponse:
    def __init__(self):
        self.deferred = False
    async def defer(self):
        self.deferred = True

class DummyInteraction:
    def __init__(self, user, bot):
        self.user = user
        self.bot = bot
        self.response = DummyResponse()

class DummyTree:
    def __init__(self):
        self.commands = {}
    def command(self, name=None, description=None):
        def decorator(func):
            cmd_name = name or func.__name__
            self.commands[cmd_name] = func
            return func
        return decorator

class DummyBot:
    def __init__(self):
        self.user = DummyUser(0)
        self.tree = DummyTree()
    async def fetch_user(self, user_id):
        return DummyUser(user_id)

@pytest.fixture
def config():
    return {
        "CURRENCY_NAME": "Pint",
        "CURRENCY_NAME_PLURAL": "Pints",
        "GET_DEBTS_COMMAND": "get_debts",
        "GET_ALL_DEBTS_COMMAND": "get_all_debts",
        "BOT_NAME": "PintBot",
        "TRANSFERABLE_ITEMS": ["Beer", "Wine"],
        "SHOW_PERCENTAGES_DEFAULT": False,
        "USE_TABLE_FORMAT_DEFAULT": True,
        "ECONOMY_HEALTH_MESSAGES": [
            {"threshold": 0, "message": "Economy is dead"},
            {"threshold": 1, "message": "Economy active"}
        ],
        "MAXIMUM_PER_DEBT": 10,
        "SMALLEST_UNIT": "0.01",
        "MAXIMUM_DEBT_CHARACTER_LIMIT": 200,
        "QUANTIZE_SETTLING_DEBTS": True
    }

@pytest.fixture
def shared():
    class Shared: pass
    shared = Shared()
    # Default fake API responses
    shared.debts_response = {'message': 'No debts'}
    shared.all_debts_response = {}
    return shared

@pytest.fixture
def bot(config):
    bot = DummyBot()
    commands.register_commands(bot, config)
    return bot

@pytest.fixture(autouse=True)
def mocks(monkeypatch, shared, config):
    # Stub unicode preference & error handler
    async def fake_fetch_unicode(interaction, user_id):
        return True
    monkeypatch.setattr(commands, 'fetch_unicode_preference', fake_fetch_unicode)

    async def fake_handle_error(interaction, *args, **kwargs):
        interaction.error = {'args': args, 'kwargs': kwargs}
    monkeypatch.setattr(commands, 'handle_error', fake_handle_error)

    # Stub formatters
    monkeypatch.setattr(commands, 'currency_formatter', lambda amount, cfg, use_unicode: str(amount))
    monkeypatch.setattr(commands, 'to_percentage', lambda amt, total, cfg: '50')

    # Stub Pydantic models
    class DummyModel:
        def __init__(self, **kwargs):
            self.kwargs = kwargs
        def model_dump(self):
            return self.kwargs
    for model in ['OweRequest', 'SettleRequest', 'SetUnicodePreferenceRequest']:
        monkeypatch.setattr(commands, model, DummyModel)

    # Fake API client
    class FakeAPI:
        def __init__(self, shared):
            self.shared = shared
            self.calls = {}
        def add_debt(self, payload):
            self.calls['add_debt'] = payload
            return {'amount': payload['amount'], 'reason': payload['reason'], 'timestamp': '2025-01-01T00:00:00Z'}
        def get_debts(self, user_id):
            return self.shared.debts_response
        def get_all_debts(self):
            return self.shared.all_debts_response
        def settle_debt(self, payload):
            self.calls['settle_debt'] = payload
            return {'settled_amount': payload['amount'], 'remaining_amount': '0'}
        def set_unicode_preference(self, payload):
            self.calls['set_unicode_preference'] = payload
            return {'message': 'Preference updated'}
    fake_api = FakeAPI(shared)
    monkeypatch.setattr(commands, 'api_client', fake_api)

    # Stub message senders, capturing all calls
    def make_stub(name):
        async def stub(interaction, *args, **kwargs):
            attr = f"{name}_calls"
            calls = getattr(interaction, attr, [])
            calls.append({'args': args, 'kwargs': kwargs})
            setattr(interaction, attr, calls)
        return stub

    for fn in [
        'send_info_message', 'send_success_message',
        'send_two_column_table_message', 'send_one_column_table_message'
    ]:
        monkeypatch.setattr(commands, fn, make_stub(fn))

# Tests
class TestHelpCommand:
    @pytest.mark.asyncio
    async def test_help_command(self, bot):
        interaction = DummyInteraction(DummyUser(1), bot)
        cmd = bot.tree.commands['help']
        await cmd(interaction)
        calls = interaction.send_info_message_calls
        assert calls, "Expected send_info_message to be called"
        kwargs = calls[0]['kwargs']
        assert kwargs['title'] == 'PintBot Help'
        assert '**/owe**' in kwargs['description']
        assert '- Beer' in kwargs['description']

class TestOweCommand:
    @pytest.mark.parametrize(
        "target_attr, error_code", [
            ("user", "CANNOT_OWE_SELF"),
            ("bot.user", "CANNOT_OWE_BOT"),
        ]
    )
    @pytest.mark.asyncio
    async def test_owe_errors(self, bot, target_attr, error_code):
        interaction = DummyInteraction(DummyUser(1), bot)
        # resolve target dynamically
        target = getattr(interaction, target_attr) if '.' not in target_attr else eval(f"interaction.{target_attr}")
        await bot.tree.commands['owe'](interaction, target, '1')
        assert interaction.error['kwargs']['error_code'] == error_code

    @pytest.mark.asyncio
    async def test_owe_success(self, bot):
        interaction = DummyInteraction(DummyUser(1), bot)
        cmd = bot.tree.commands['owe']
        target = DummyUser(2)
        await cmd(interaction, target, '3', reason='Test')
        # verify API call payload
        assert commands.api_client.calls['add_debt'] == {
            'debtor': 1, 'creditor': 2, 'amount': '3', 'reason': 'Test'
        }
        calls = interaction.send_success_message_calls
        assert calls, "Expected send_success_message to be called"
        kwargs = calls[0]['kwargs']
        assert kwargs['title'] == 'Pint Debt Added - Pint Economy Thriving'
        assert '3' in kwargs['description']

class TestGetDebtsCommand:
    @pytest.mark.asyncio
    async def test_get_debts_with_debts(self, bot, config, shared):
        interaction = DummyInteraction(DummyUser(1), bot)
        cmd = bot.tree.commands[config['GET_DEBTS_COMMAND']]

        # With debts
        shared.debts_response = {
            'owed_by_you': {'2': [{'amount': '1', 'reason': 'Test', 'timestamp': '2025-01-01'}]},
            'total_owed_by_you': '1',
            'owed_to_you': {'3': [{'amount': '2', 'reason': 'Other', 'timestamp': '2025-01-02'}]},
            'total_owed_to_you': '2'
        }
        await cmd(interaction)
        info_calls = interaction.send_info_message_calls
        assert info_calls
        title = info_calls[0]['kwargs']['title']
        desc = info_calls[0]['kwargs']['description']
        assert 'Your Pint debts' in title
        assert '**User2**: 1' in desc
        assert '- 1 for *Test* on 2025-01-01' in desc
        assert '**User3**: 2' in desc

    @pytest.mark.asyncio
    async def test_get_debts_no_debts(self, bot, config, shared):
        interaction = DummyInteraction(DummyUser(1), bot)
        cmd = bot.tree.commands[config['GET_DEBTS_COMMAND']]

        # No debts
        shared.debts_response = {'message': 'No debts'}
        await cmd(interaction)
        info_calls = interaction.send_info_message_calls
        assert info_calls
        assert 'not currently contributing to the Pint economy' in info_calls[0]['kwargs']['title']

class TestGetAllDebtsCommand:
    @pytest.mark.asyncio
    async def test_get_all_debts_success(self, bot, config, shared):
        interaction = DummyInteraction(DummyUser(1), bot)
        cmd = bot.tree.commands[config['GET_ALL_DEBTS_COMMAND']]

        # With data
        shared.all_debts_response = {
            'total_in_circulation': '3',
            '1': {'owes': '1', 'is_owed': '2'},
            '2': {'owes': '0', 'is_owed': '1'}
        }
        await cmd(interaction)
        table_calls = interaction.send_two_column_table_message_calls
        assert table_calls
        kwargs = table_calls[0]['kwargs']
        assert kwargs['title'] == 'Pint Economy Overview'
        assert 'Economy active' in kwargs['description']
        assert '**Total Pints in circulation: 3**' in kwargs['description']
        names = [row['name'] for row in kwargs['data']]
        assert 'User1' in names and 'User2' in names

    @pytest.mark.asyncio
    async def test_get_all_debts_no_debts_error(self, bot, config, shared):
        interaction = DummyInteraction(DummyUser(1), bot)
        cmd = bot.tree.commands[config['GET_ALL_DEBTS_COMMAND']]

        # Simulate no debts in the economy
        shared.all_debts_response = {'total_in_circulation': '0'}
        await cmd(interaction)

        # Expect handle_error to be invoked with NO_DEBTS_IN_ECONOMY
        assert hasattr(interaction, 'error'), "Expected handle_error to be called for no debts"
        assert interaction.error['kwargs']['error_code'] == 'NO_DEBTS_IN_ECONOMY'
class TestSettleCommand:
    @pytest.mark.parametrize(
        "target_attr, error_code", [
            ("user", "CANNOT_SETTLE_SELF"),
            ("bot.user", "CANNOT_SETTLE_BOT"),
        ]
    )
    @pytest.mark.asyncio
    async def test_settle_errors(self, bot, target_attr, error_code):
        interaction = DummyInteraction(DummyUser(1), bot)
        target = eval(f"interaction.{target_attr}")
        await bot.tree.commands['settle'](interaction, target, '1')
        assert interaction.error['kwargs']['error_code'] == error_code

    @pytest.mark.asyncio
    async def test_settle_success(self, bot):
        interaction = DummyInteraction(DummyUser(1), bot)
        cmd = bot.tree.commands['settle']

        # Success
        target = DummyUser(2)
        await cmd(interaction, target, '5')
        assert commands.api_client.calls['settle_debt'] == {
            'debtor': 1, 'creditor': 2, 'amount': '5'
        }
        calls = interaction.send_success_message_calls
        assert calls
        assert 'Settled 5 with <@2>' in calls[0]['kwargs']['description']

class TestSetUnicodePreferenceCommand:
    @pytest.mark.asyncio
    async def test_set_unicode_preference(self, bot):
        interaction = DummyInteraction(DummyUser(1), bot)
        cmd = bot.tree.commands['set_unicode_preference']

        await cmd(interaction, True)
        assert commands.api_client.calls['set_unicode_preference'] == {'user_id': 1, 'use_unicode': True}
        calls = interaction.send_success_message_calls
        assert calls
        assert calls[0]['kwargs']['title'] == 'Preference Updated'
        assert calls[0]['kwargs']['description'] == 'Preference updated'

class TestSettingsCommand:
    @pytest.mark.asyncio
    async def test_settings_command(self, bot):
        interaction = DummyInteraction(DummyUser(1), bot)
        cmd = bot.tree.commands['settings']
        
        await cmd(interaction)
        calls = interaction.send_one_column_table_message_calls
        assert len(calls) == 2
        bot_cfg = calls[0]['kwargs']['data']
        api_cfg = calls[1]['kwargs']['data']
        assert any(item['Setting'] == 'CURRENCY_NAME' for item in bot_cfg)
        assert any(item['Setting'] == 'Maximum Debt Per Transaction' for item in api_cfg)
