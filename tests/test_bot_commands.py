from unittest.mock import patch
import pytest
import bot.bot_commands as commands
from bot.command import Command
from types import SimpleNamespace

# Dummy Discord objects for testing
class DummyUser:
    def __init__(self, id, display_name=None):
        self.id = id
        self.display_name = display_name or f'User{self.id}'
        self.mention = f'<@{self.id}>'
    def __str__(self):
        return self.mention

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
        self.error = None
        self.send_info_message_calls = []
        self.send_success_message_calls = []
        self.send_two_column_table_message_calls = []
        self.send_one_column_table_message_calls = []

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
def shared():
    class Shared: pass
    shared = Shared()
    shared.debts_response = {'message': 'No debts'}
    shared.all_debts_response = {}
    return shared

@pytest.fixture(autouse=True)
def mocks(monkeypatch, shared):
    # Mock utility functions
    async def fake_fetch_unicode(interaction, user_id):
        return True

    async def fake_handle_error(interaction, *args, **kwargs):
        interaction.error = {'args': args, 'kwargs': kwargs}

    monkeypatch.setattr(commands, 'fetch_unicode_preference', fake_fetch_unicode)
    monkeypatch.setattr(commands, 'handle_error', fake_handle_error)
    monkeypatch.setattr(commands, 'currency_formatter', lambda amount, use_unicode: str(amount))
    monkeypatch.setattr(commands, 'to_percentage', lambda amt, total, cfg: '50')

    # Mock command categories
    fake_commands = {
        "Core": [
            SimpleNamespace(name="owe", description="See what you owe"),
            SimpleNamespace(name="settle", description="Settle up"),
        ],
        "Fun": [
            SimpleNamespace(name="gift", description="Gift a debt"),
        ]
    }
    monkeypatch.setattr(Command, "all_by_category", lambda: fake_commands)

    # Mock models
    class DummyModel:
        def __init__(self, **kwargs):
            self.kwargs = kwargs
        def model_dump(self):
            return self.kwargs

    for model in [
        'OweRequest',
        'SettleRequest',
        'SetUnicodePreferenceRequest',
        'DebtsWithUser'
    ]:
        monkeypatch.setattr(commands, model, DummyModel)

    # Mock API client
    class FakeAPI:
        def __init__(self, shared):
            self.shared = shared
            self.calls = {}

        def add_debt(self, payload):
            self.calls['add_debt'] = payload
            return {
                'amount': payload['amount'],
                'reason': payload['reason'],
                'timestamp': '2025-01-01T00:00:00Z'
            }

        def get_debts(self, user_id):
            return self.shared.debts_response

        def get_all_debts(self):
            return self.shared.all_debts_response

        def debts_with_user(self, payload):
            self.calls['debts_with_user'] = payload
            return self.shared.debts_response

        def settle_debt(self, payload):
            self.calls['settle_debt'] = payload
            return {'settled_amount': payload['amount'], 'remaining_amount': '0'}

        def set_unicode_preference(self, payload):
            self.calls['set_unicode_preference'] = payload
            return {'message': 'Preference updated'}

    monkeypatch.setattr(commands, 'api_client', FakeAPI(shared))

    # Mock message sending functions
    def make_stub(name):
        async def stub(interaction, *args, **kwargs):
            attr = f"{name}_calls"
            calls = getattr(interaction, attr, [])
            calls.append({'args': args, 'kwargs': kwargs})
            setattr(interaction, attr, calls)
        return stub

    for fn in [
        'send_info_message',
        'send_success_message',
        'send_two_column_table_message',
        'send_one_column_table_message',
    ]:
        monkeypatch.setattr(commands, fn, make_stub(fn))

@pytest.fixture
def bot():
    bot = DummyBot()
    commands.register_commands(bot)
    return bot

# Tests

class TestRegistration:
    def test_commands_registered(self, bot):
        import bot.config as config
        expected = {
            'help',
            'owe',
            config.GET_DEBTS_COMMAND,
            config.GET_ALL_DEBTS_COMMAND,
            config.DEBTS_WITH_USER_COMMAND,
            'settle',
            'set_unicode_preference',
            config.ROLL_COMMAND,
            'settings',
        }
        assert set(bot.tree.commands.keys()) == expected

class TestHelpCommand:
    @pytest.mark.asyncio
    async def test_help_commands_section(self, bot):
        import bot.config as config
        interaction = DummyInteraction(DummyUser(1), bot)

        cmd = bot.tree.commands["help"]
        await cmd(interaction)

        assert interaction.response.deferred
        msg = interaction.send_info_message_calls[0]['kwargs']['description']

        # Use the same fake_commands defined in the fixture
        for category in ["Core", "Fun"]:
            assert f"**{category}:**" in msg
        for command in [
            ("owe", "See what you owe"),
            ("settle", "Settle up"),
            ("gift", "Gift a debt"),
        ]:
            assert f"**/{command[0]}** — {command[1]}" in msg

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


class TestOweCommand:
    @pytest.mark.parametrize(
        "target_attr, error_code", [
            ("user", "CANNOT_OWE_SELF"),
            ("bot.user", "CANNOT_OWE_BOT"),
        ],
        ids=["cant_owe_self", "cant_owe_bot"]
    )
    @pytest.mark.asyncio
    async def test_owe_errors(self, bot, target_attr, error_code):
        interaction = DummyInteraction(DummyUser(1), bot)
        target = eval(f"interaction.{target_attr}")
        await bot.tree.commands['owe'](interaction, target, '1')
        assert interaction.error['kwargs']['error_code'] == error_code

    @pytest.mark.asyncio
    async def test_owe_success_and_defer(self, bot):
        interaction = DummyInteraction(DummyUser(1), bot)
        target = DummyUser(2)
        await bot.tree.commands['owe'](interaction, target, '3', reason='Test')
        assert interaction.response.deferred
        assert commands.api_client.calls['add_debt'] == {
            'debtor': 1, 'creditor': 2, 'amount': '3', 'reason': 'Test'
        }
        calls = interaction.send_success_message_calls
        assert calls
        kwargs = calls[0]['kwargs']
        assert '3' in kwargs['description']

class TestGetDebtsCommand:
    @pytest.mark.parametrize("response, expected_title", [
        ({'message': 'No debts'}, "you're not currently contributing to the TestCoin economy"),
        ({
            'owed_by_you': {'2': [{'amount': '1', 'reason': 'Test', 'timestamp': '2025-01-01'}]},
            'total_owed_by_you': '1',
            'owed_to_you': {'3': [{'amount': '2', 'reason': 'Other', 'timestamp': '2025-01-02'}]},
            'total_owed_to_you': '2'
        }, "Your TestCoin debts"),
        ({'message': 'No debts'}, "they're not currently contributing to the TestCoin economy"),
        ({
            'owed_by_you': {'2': [{'amount': '1', 'reason': 'Test', 'timestamp': '2025-01-01'}]},
            'total_owed_by_you': '1',
            'owed_to_you': {'3': [{'amount': '2', 'reason': 'Other', 'timestamp': '2025-01-02'}]},
            'total_owed_to_you': '2'
        }, "Here are fake name's TestCoin debts"),
    ], ids=["self_no_debts", "self_with_debts", "other_no_debts", "other_with_debts"])
    @pytest.mark.asyncio
    async def test_get_debts_titles(self, bot, shared, response, expected_title):
        import bot.config as config
        shared.debts_response = response
        interaction = DummyInteraction(DummyUser(1), bot)
        cmd = bot.tree.commands[config.GET_DEBTS_COMMAND]
        await cmd(interaction, user=None if 'you' in expected_title.lower() else DummyUser(123, display_name="fake name"))
        assert interaction.response.deferred
        info_calls = interaction.send_info_message_calls
        assert info_calls
        title = info_calls[0]['kwargs']['title']
        assert expected_title in title
    
    @pytest.mark.parametrize("show_details, show_percentages, expected_checks", [
        # Each tuple is: (expected_text, should_be_present)
        # Used to verify whether specific content appears in the command output.
        # For example, if show_details=False, then detailed lines shouldn't appear.

        # Summary only (no detail lines)
        (False, False, [("**User4**: 2", True), ("- 1 for *Coffee*", False), ("- 1 for *Beer*", False)]),

        # Detailed breakdown without percentages
        (True, False, [("- 1 for *Coffee* on 2025-01-01", True), ("- 1 for *Beer* on 2025-01-02", True), ("50", False)]),

        # Detailed breakdown with percentages (mocked to '50')
        (True, True, [("- 1 50 for *Coffee* on 2025-01-01", True), ("- 1 50 for *Beer* on 2025-01-02", True)]),
    ], ids=["summary_only", "details_no_percentages", "details_with_percentages"])
    @pytest.mark.asyncio
    async def test_get_debts_optional_variants(self, bot, shared, show_details, show_percentages, expected_checks):
        """
        Tests combinations of 'show_details' and 'show_percentages' flags for get_debts.

        Each test case provides:
        - Whether details and/or percentages are enabled
        - A list of (text, should_exist) pairs to assert presence/absence in the output
        """
        import bot.config as config

        shared.debts_response = {
            'owed_by_you': {'4': [
                {'amount': '1', 'reason': 'Coffee', 'timestamp': '2025-01-01'},
                {'amount': '1', 'reason': 'Beer', 'timestamp': '2025-01-02'},
            ]},
            'total_owed_by_you': '2',
            'owed_to_you': {},
            'total_owed_to_you': '0'
        }

        interaction = DummyInteraction(DummyUser(1), bot)
        cmd = bot.tree.commands[config.GET_DEBTS_COMMAND]
        await cmd(interaction, show_details=show_details, show_percentages=show_percentages)
        description = interaction.send_info_message_calls[0]['kwargs']['description']

        for text, should_exist in expected_checks:
            if should_exist:
                assert text in description
            else:
                assert text not in description

class TestGetAllDebtsCommand:
    @pytest.mark.parametrize("response, expect_error, health_msg", [
        ({'total_in_circulation': '0'}, True, None),
        ({
            'total_in_circulation': '3',
            '1': {'owes': '1', 'is_owed': '2'},
            '2': {'owes': '0', 'is_owed': '1'}
        }, False, 'Economy active'),
    ],
    ids=["no_debts_in_economy", "debts_in_economy"])
    @patch.multiple(
        "bot.config",
        ECONOMY_HEALTH_MESSAGES=[
            {"threshold": 0, "message": "Economy is dead"},
            {"threshold": 1, "message": "Economy active"},
        ],
    )
    @pytest.mark.asyncio
    async def test_get_all_debts_various(self, bot, shared, response, expect_error, health_msg):
        import bot.config as config
        interaction = DummyInteraction(DummyUser(1), bot)
        shared.all_debts_response = response
        cmd = bot.tree.commands[config.GET_ALL_DEBTS_COMMAND]
        await cmd(interaction)
        assert interaction.response.deferred
        if expect_error:
            assert hasattr(interaction, 'error')
            assert interaction.error['kwargs']['error_code'] == 'NO_DEBTS_IN_ECONOMY'
        else:
            table_calls = interaction.send_two_column_table_message_calls
            assert table_calls
            description = table_calls[0]['kwargs']['description']
            assert health_msg in description

class TestDebtsWithUserCommand:
    @pytest.mark.asyncio
    async def test_no_debts_message(self, bot, shared):
        import bot.config as config
        shared.api_response = {"message": "No debts"}
        shared.debts_response = shared.api_response

        interaction = DummyInteraction(DummyUser(1), bot)
        other_user = DummyUser(2)
        await bot.tree.commands[config.DEBTS_WITH_USER_COMMAND](interaction, user=other_user)

        assert interaction.response.deferred
        calls = interaction.send_info_message_calls
        assert calls
        kwargs = calls[0]['kwargs']
        assert f"no {config.CURRENCY_NAME} debts" in kwargs["title"]
        assert "kind of cringe" in kwargs["description"]

    @pytest.mark.asyncio
    async def test_debts_with_user_with_details_and_percentages(self, bot, shared):
        import bot.config as config
        shared.api_response = {
            'owed_by_you': [
                {'amount': '1', 'reason': 'being silly', 'timestamp': '2025-01-01'}
            ],
            'total_owed_by_you': '1',
            'owed_to_you': [
                {'amount': '2', 'reason': 'for passing exams', 'timestamp': '2025-01-02'}
            ],
            'total_owed_to_you': '2',
        }
        shared.debts_response = shared.api_response

        interaction = DummyInteraction(DummyUser(1, display_name="Alice"), bot)
        other_user = DummyUser(2, display_name="Bob")
        await bot.tree.commands[config.DEBTS_WITH_USER_COMMAND](
            interaction,
            user=other_user,
            show_details=True,
            show_percentages=True
        )

        assert interaction.response.deferred
        calls = interaction.send_info_message_calls
        assert calls
        kwargs = calls[0]['kwargs']
        assert "Alice" in kwargs["title"]
        assert "Bob" in kwargs["title"]
        description = kwargs["description"]
        assert "1" in description and "being silly" in description
        assert "2" in description and "for passing exams" in description
        assert "50" in description  # mocked percentage

    @pytest.mark.asyncio
    async def test_error_handling(self, bot, monkeypatch):
        import bot.config as config
        def broken_api_call(_):
            raise Exception("Boom")

        monkeypatch.setattr(commands.api_client, "debts_with_user", broken_api_call)

        interaction = DummyInteraction(DummyUser(1), bot)
        other_user = DummyUser(2)
        await bot.tree.commands[config.DEBTS_WITH_USER_COMMAND](interaction, user=other_user)

        assert interaction.response.deferred
        assert hasattr(interaction, 'error')
        assert "Boom" in str(interaction.error['args'][0])

class TestSettleCommand:
    @pytest.mark.parametrize(
        "target_attr, error_code", [
            ("user", "CANNOT_SETTLE_SELF"),
            ("bot.user", "CANNOT_SETTLE_BOT"),
        ],
        ids=["cant_settle_self", "cant_settle_bot"]
    )
    @pytest.mark.asyncio
    async def test_settle_errors(self, bot, target_attr, error_code):
        interaction = DummyInteraction(DummyUser(1), bot)
        target = eval(f"interaction.{target_attr}")
        await bot.tree.commands['settle'](interaction, target, '1')
        assert interaction.error['kwargs']['error_code'] == error_code

    @pytest.mark.asyncio
    async def test_settle_success_and_defer(self, bot):
        interaction = DummyInteraction(DummyUser(1), bot)
        target = DummyUser(2)
        await bot.tree.commands['settle'](interaction, target, '5')
        assert interaction.response.deferred
        assert commands.api_client.calls['settle_debt'] == {
            'debtor': 1, 'creditor': 2, 'amount': '5'
        }
        calls = interaction.send_success_message_calls
        assert calls
        assert 'Settled 5 with <@2>' in calls[0]['kwargs']['description']

class TestSetUnicodePreferenceCommand:
    @pytest.mark.parametrize("pref", [True, False])
    @pytest.mark.asyncio
    async def test_set_unicode_preference(self, bot, pref):
        interaction = DummyInteraction(DummyUser(1), bot)
        await bot.tree.commands['set_unicode_preference'](interaction, pref)
        assert commands.api_client.calls['set_unicode_preference'] == {'user_id': "1", 'use_unicode': pref}
        calls = interaction.send_success_message_calls
        assert calls
        assert calls[0]['kwargs']['title'] == 'Preference Updated'

class TestRollCommand:
    @pytest.mark.asyncio
    async def test_roll_win(self, bot, monkeypatch):
        import bot.config as config

        # Force a winning roll
        monkeypatch.setattr(config.RANDOM_NUMBER_GENERATOR, "randint", lambda a, b: config.ROLL_WINNING_NUMBER)

        interaction = DummyInteraction(DummyUser(42), bot)
        cmd = bot.tree.commands[config.ROLL_COMMAND]
        await cmd(interaction)

        assert interaction.response.deferred

        # Check success message
        calls = interaction.send_success_message_calls
        assert len(calls) == 1
        kwargs = calls[0]["kwargs"]

        expected_title = f"WINNER! You rolled {config.ROLL_WINNING_NUMBER}!"
        expected_description = (
            f"Congratulations {interaction.user.mention}!\n"
            f"You won the {config.ROLL_COMMAND} game!\n"
        )

        assert kwargs["title"] == expected_title
        assert kwargs["description"] == expected_description

    @pytest.mark.asyncio
    async def test_roll_loss(self, bot, monkeypatch):
        import bot.config as config

        # Force a non-winning roll
        losing_number = max(1, config.ROLL_WINNING_NUMBER - 1)
        monkeypatch.setattr(config.RANDOM_NUMBER_GENERATOR, "randint", lambda a, b: losing_number)

        interaction = DummyInteraction(DummyUser(99), bot)
        cmd = bot.tree.commands[config.ROLL_COMMAND]
        await cmd(interaction)

        assert interaction.response.deferred

        # Check info message
        calls = interaction.send_info_message_calls
        assert len(calls) == 1
        kwargs = calls[0]["kwargs"]

        expected_title = f"You rolled {losing_number}."
        expected_description = (
            f"Sorry {interaction.user.mention}, that's not a winning number.\n"
            "Better luck next time!"
        )

        assert kwargs["title"] == expected_title
        assert kwargs["description"] == expected_description


class TestSettingsCommand:
    @pytest.mark.asyncio
    async def test_settings_command(self, bot):
        interaction = DummyInteraction(DummyUser(1), bot)
        await bot.tree.commands['settings'](interaction)
        calls = interaction.send_one_column_table_message_calls
        assert len(calls) == 1
        bot_cfg = calls[0]['kwargs']['data']
        assert any(item['Setting'] == 'Currency Name' for item in bot_cfg)
