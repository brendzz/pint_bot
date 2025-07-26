from unittest.mock import patch
import pytest
from datetime import datetime

from bot import config
from tests.conftest import DummyInteraction, DummyUser
from fractions import Fraction

class TestGetDebtsCommand:
    @pytest.mark.parametrize("response, expected_title", [
        ({'message': 'No debts'}, "you're not currently contributing to the TestCoin economy"),
        ({
            'owed_by_you': {'2': [{'amount': '1', 'reason': 'Test', 'timestamp': '02-01-2025'}]},
            'total_owed_by_you': '1',
            'owed_to_you': {'3': [{'amount': '2', 'reason': 'Other', 'timestamp': '02-01-2025'}]},
            'total_owed_to_you': '2'
        }, "Your TestCoin debts"),
        ({'message': 'No debts'}, "they're not currently contributing to the TestCoin economy"),
        ({
            'owed_by_you': {'2': [{'amount': '1', 'reason': 'Test', 'timestamp': '02-01-2025'}]},
            'total_owed_by_you': '1',
            'owed_to_you': {'3': [{'amount': '2', 'reason': 'Other', 'timestamp': '02-01-2025'}]},
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
        calls = interaction.send_info_message_calls
        assert calls
        title = calls[0]['kwargs']['title']
        assert expected_title in title
    
    @pytest.mark.parametrize("show_details, show_percentages, show_conversion_currency, show_emoji_visuals, expected_checks", [
        # Each tuple is: (expected_text, should_be_present)
        # Used to verify whether specific content appears in the command output.
        # For example, if show_details=False, then detailed lines shouldn't appear.

        # Summary only (no detail lines)
        (False, False, False, False, [("__**TestCoins YOU OWE:**__ 2 TESTCOINS", True), ("**User4:** 2 testcoins", True), ("- 1 testcoin for *Coffee*", False), ("- 1 testcoin for *Beer*", False)]),

        # Detailed breakdown without percentages or conversion currency
        (True, False, False, False, [("- 1 testcoin for *Coffee* on 02-01-2025", True), ("- 1 testcoin for *Beer* on 02-01-2025", True), ("50", False), ("£6", False), ("🍺", False)]),

        # Detailed breakdown with percentages (mocked to '50')
        (True, True, False, False, [("- 1 testcoin 50 for *Coffee* on 02-01-2025", True), ("- 1 testcoin 50 for *Beer* on 02-01-2025", True), ("£6", False)]),

        # Breakdown with conversion currency and details
        (True, False, True, False, [("__**TestCoins YOU OWE:**__ 2 TESTCOINS [£12]", True), ("- 1 testcoin [£6]", True), ("- 1 testcoin [£6]", True), ("50", False)]),

        # Breakdown with everything
        (True, True, True, True, [("[£12]\n🍺🍺", True), ("- 1 testcoin [£6] 50🍺 for *Coffee*", True)]),

    ], ids=["summary_only", "details_no_percentages", "details_with_percentages", "with_conversion_currency", "with_emoji_visual"])
    @pytest.mark.asyncio
    async def test_get_debts_optional_variants(self, bot, shared, show_details, show_percentages, show_conversion_currency, show_emoji_visuals, expected_checks):
        """
        Tests combinations of 'show_details' and 'show_percentages' flags for get_debts.

        Each test case provides:
        - Whether details and/or percentages are enabled
        - A list of (text, should_exist) pairs to assert presence/absence in the output
        """

        shared.debts_response = {
            'owed_by_you': {'4': [
                {'amount': '1', 'reason': 'Coffee', 'timestamp': '2025-01-02'},
                {'amount': '1', 'reason': 'Beer', 'timestamp': '2025-01-02'},
            ]},
            'total_owed_by_you': '2',
            'owed_to_you': {},
            'total_owed_to_you': '0'
        }

        interaction = DummyInteraction(DummyUser(1), bot)
        cmd = bot.tree.commands[config.GET_DEBTS_COMMAND]
        await cmd(interaction,
                  show_details=show_details,
                  show_percentages=show_percentages,
                  show_conversion_currency=show_conversion_currency,
                  show_emoji_visuals=show_emoji_visuals)
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
    @patch(
        "bot.utilities.flavour_messages.ECONOMY_HEALTH_MESSAGES",
        [
            {"threshold": Fraction(1), "message": "Economy active"},
            {"threshold": Fraction(0), "message": "Economy is dead"}
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
            assert interaction.error is not None
            assert interaction.error['kwargs']['error_code'] == 'NO_DEBTS_IN_ECONOMY'
        else:
            table_calls = interaction.send_two_column_table_message_calls
            assert table_calls
            description = table_calls[0]['kwargs']['description']
            assert health_msg in description

class TestDebtsWithUserCommand:
    @pytest.mark.asyncio
    async def test_no_debts_message(self, bot, shared):
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
        shared.api_response = {
            'owed_by_you': [
                {'amount': '1', 'reason': 'being silly', 'timestamp': '02-01-2025'}
            ],
            'total_owed_by_you': '1',
            'owed_to_you': [
                {'amount': '3', 'reason': 'for passing exams', 'timestamp': '02-01-2025'}
            ],
            'total_owed_to_you': '3',
        }
        shared.debts_response = shared.api_response

        interaction = DummyInteraction(DummyUser(1, display_name="Alice"), bot)
        other_user = DummyUser(2, display_name="Bob")
        await bot.tree.commands[config.DEBTS_WITH_USER_COMMAND](
            interaction,
            user=other_user,
            show_details=True,
            show_percentages=True,
            show_conversion_currency=False
        )

        assert interaction.response.deferred
        calls = interaction.send_info_message_calls
        assert calls
        kwargs = calls[0]['kwargs']
        assert "Alice" in kwargs["title"]
        assert "Bob" in kwargs["title"]
        description = kwargs["description"]
        assert "1" in description and "being silly" in description
        assert "3" in description and "for passing exams" in description
        assert "50" in description  # mocked percentage
        assert "2" in description and "positive" in description # net total

    @patch("bot.commands.debt_display.handle_error")
    @pytest.mark.asyncio
    async def test_error_handling(self, mock_handle_error, bot, monkeypatch):
        def broken_api_call(_):
            raise Exception("Boom")

        monkeypatch.setattr("bot.commands.debt_display.api_client.debts_with_user", broken_api_call)

        interaction = DummyInteraction(DummyUser(1), bot)
        other_user = DummyUser(2)

        await bot.tree.commands[config.DEBTS_WITH_USER_COMMAND](interaction, user=other_user)

        mock_handle_error.assert_called_once()

class TestTransactionsCommand:
    @pytest.mark.asyncio
    async def test_transactions_command_basic(self, bot, shared):
        # Mock API response for transactions
       
        shared.transactions_response = {
            "start_date": "2025-01-01",
            "end_date": "2025-01-31",
            "transactions": [
                {
                    "type": "owe",
                    "debtor": "1",
                    "creditor": "2",
                    "amount": "5",
                    "reason": "Lunch",
                    "timestamp": "2025-01-02T12:00:00"
                },
                {
                    "type": "settle",
                    "debtor": "2",
                    "creditor": "1",
                    "amount": "3",
                    "reason": "Repayment",
                    "timestamp": "2025-01-03T15:30:00"
                }
            ]
        }
        
        interaction = DummyInteraction(DummyUser(1), bot)
        cmd = bot.tree.commands["transactions"]
        await cmd(interaction)

        # Check that the response was deferred
        assert interaction.response.deferred

        # Check that an info message was sent
        calls = interaction.send_info_message_calls
        assert calls
        title = calls[0]['kwargs']['title']
        description = calls[0]['kwargs']['description']

        # Basic checks for expected content
        assert "Transactions from" in title
        assert "Lunch" in description
        assert "Repayment" in description
        assert "Total Owed In Period" in description
        assert "Total Settled In Period" in description
