import sys
import os

# Add the project root to the import path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Add the bot folder to the import path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'bot')))

from unittest.mock import patch
from fractions import Fraction
import pytest

import bot.register_commands as register_commands
from bot.commands import debt_display, debt_management, settings
from bot.utilities import send_messages, user_preferences

# Static config overrides for testing
PATCHED_CONFIG = {
    "CURRENCY_NAME": "TestCoin",
    "CURRENCY_NAME_PLURAL": "TestCoins",
    "BOT_NAME": "TestBot",
    "GET_DEBTS_COMMAND": "testcoins",
    "GET_ALL_DEBTS_COMMAND": "all_testcoins",
    "DEBTS_WITH_USER_COMMAND": "testcoins_with_user",
    "TRANSFERABLE_ITEMS": ["Beer", "Wine"],
    "SHOW_PERCENTAGES_DEFAULT": False,
    "USE_TABLE_FORMAT_DEFAULT": True,
    "ECONOMY_HEALTH_MESSAGES": [
        {"threshold": 0, "message": "Economy is dead"},
        {"threshold": 1, "message": "Economy active"},
    ],
    "MAXIMUM_PER_DEBT": 10,
    "SMALLEST_UNIT": Fraction(1, 6),
    "MAXIMUM_DEBT_CHARACTER_LIMIT": 200,
    "QUANTIZE_SETTLING_DEBTS": True,
    "SHOW_DETAILS_DEFAULT": True,
}

# Global config patching (applies to all tests)
@pytest.fixture(autouse=True, scope="session")
def patch_config_before_tests():
    with patch.multiple("bot.utilities.error_handling.config", **PATCHED_CONFIG), \
         patch.multiple("bot.utilities.formatter.config", **PATCHED_CONFIG), \
         patch.multiple("bot.register_commands.config", **PATCHED_CONFIG):
        yield

@pytest.fixture(autouse=True)
def reset_command_registry():
    # Clear and re-register commands before each test
    register_commands.define_command_details()

# Fake API client
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

# Dummy Discord classes
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

class DummyFollowup:
    def __init__(self):
        self.sent = False
    async def send(self, *args, **kwargs):
        self.sent = True

class DummyInteraction:
    def __init__(self, user, bot):
        self.user = user
        self.client = bot
        self.response = DummyResponse()
        self.followup = DummyFollowup()
        self.send_info_message_calls = []
        self.send_success_message_calls = []
        self.send_two_column_table_message_calls = []
        self.send_one_column_table_message_calls = []
        self.error = None

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

    @property
    def id(self):
        return self.user.id

    async def fetch_user(self, user_id):
        return DummyUser(user_id)

# Auto applied mocks for utilities, models, API client, and messaging
@pytest.fixture(autouse=True)
def mock_bot_dependencies(monkeypatch, shared):
    # Utility function mocks
    async def fake_fetch_unicode(interaction, user_id):
        return True

    async def fake_handle_error(interaction, *args, **kwargs):
        interaction.error = {'args': args, 'kwargs': kwargs}
        print("[DEBUG] fake_handle_error triggered")

    monkeypatch.setattr(user_preferences, 'fetch_unicode_preference', fake_fetch_unicode)
    monkeypatch.setattr(debt_management, 'handle_error', fake_handle_error)
    monkeypatch.setattr(debt_display, 'handle_error', fake_handle_error)
    monkeypatch.setattr(debt_display, 'currency_formatter', lambda amount, use_unicode: str(amount))
    monkeypatch.setattr(debt_display, 'to_percentage', lambda amt, total, cfg: '50')

    # Model mocks
    class DummyModel:
        def __init__(self, **kwargs):
            self.kwargs = kwargs
        def model_dump(self):
            return self.kwargs

    model_patch_targets = {
        debt_management: ['OweRequest', 'SettleRequest'],
        debt_display: ['DebtsWithUser'],
        settings: ['SetUnicodePreferenceRequest'],
    }

    for module, model_names in model_patch_targets.items():
        for model_name in model_names:
            monkeypatch.setattr(module, model_name, DummyModel)

    monkeypatch.setattr(debt_management, 'api_client', shared.fake_api)
    monkeypatch.setattr(debt_display, 'api_client', shared.fake_api)
    monkeypatch.setattr(settings, 'api_client', shared.fake_api)
    
# Shared state for mocks
@pytest.fixture(scope="session")
def shared():
    class Shared: pass
    shared = Shared()
    shared.debts_response = {'message': 'No debts'}
    shared.all_debts_response = {}
    shared.fake_api = FakeAPI(shared)

    return shared

@pytest.fixture(autouse=True)
def patch_all_message_senders(monkeypatch):
    """
    Intercept every send_*_message in bot.utilities.send_messages
    so that tests can just inspect interaction.send_*_message_calls.
    """
    def make_stub(name):
        async def stub(interaction, *args, **kwargs):
            calls = getattr(interaction, f"{name}_calls", [])
            calls.append({'args': args, 'kwargs': kwargs})
            setattr(interaction, f"{name}_calls", calls)
        return stub

    for fn in (
        "send_info_message",
        "send_success_message",
        "send_two_column_table_message",
        "send_one_column_table_message",
        "send_error_message",
    ):
        monkeypatch.setattr(send_messages, fn, make_stub(fn))

    import importlib
    import bot.commands.support
    importlib.reload(bot.commands.support)

# Bot fixture with registered commands
@pytest.fixture
def bot(mock_bot_dependencies):
    bot = DummyBot()
    register_commands.register_commands(bot)
    return bot
