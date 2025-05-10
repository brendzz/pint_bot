import pytest
from unittest.mock import patch, AsyncMock, MagicMock, PropertyMock
from discord import Message, User
from bot.pint_bot import bot, on_message

class TestOnMessage:
    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "random_side_effect, expected_reaction",
        [
            ([0.1, 0.1], "🍻"),
            ([0.1, 1.0], "🍺"),
            ([1.0, 1.0], None),
        ],
        ids=["rare_reaction", "common_reaction","no_reaction"]
    )
    @patch("pint_bot.random.random")
    async def test_on_message_reacts_to_currency(self, mock_random, random_side_effect, expected_reaction):
        mock_random.side_effect = random_side_effect

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
