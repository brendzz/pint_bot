import pytest
from tests.conftest import DummyInteraction, DummyUser

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
        losing_number = 1 if config.ROLL_WINNING_NUMBER != 1 else 2
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