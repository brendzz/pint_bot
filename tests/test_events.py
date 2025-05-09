import pytest
from unittest.mock import patch, AsyncMock, MagicMock, PropertyMock
from discord import Message, User
from bot.pint_bot import bot, on_message

class TestOnMessage:
    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "randint_side_effect, expected_reaction",
        [
            ([2, 1], "🍺"),   # Common emoji triggered
            ([1], "🍻"),      # Rare emoji triggered
            ([2, 2], None),   # Neither triggered
        ],
        ids=["common_emoji", "rare_emoji", "no_reaction"]
    )
    @patch("pint_bot.get_config")
    @patch("pint_bot.random.randint")
    async def test_on_message_reacts_to_currency(
        self, mock_randint, mock_get_config, randint_side_effect, expected_reaction
    ):
        mock_randint.side_effect = randint_side_effect

        mock_get_config.return_value = {
            "REACT_TO_MESSAGES_MENTIONING_CURRENCY": True,
            "CURRENCY_NAME": "Pint",
            "REACTION_EMOJI": "🍺",
            "REACTION_EMOJI_RARE": "🍻",
            "BOT_NAME": "Pint Bot",
            "ODDS": 10
        }

        mock_message = AsyncMock(spec=Message)
        mock_message.content = "I love pints!"
        mock_message.add_reaction = AsyncMock()

        with patch.object(type(bot), 'user', new_callable=PropertyMock) as mock_user:
            mock_user.return_value = MagicMock(id=999)
            mock_message.author = MagicMock(id=123)

            await on_message(mock_message)

        if expected_reaction is None:
            mock_message.add_reaction.assert_not_called()
        else:
            mock_message.add_reaction.assert_called_once_with(expected_reaction)
