import pytest
from unittest.mock import patch, AsyncMock, MagicMock, PropertyMock
from discord import Message, User
from pint_bot import bot, on_message

class TestOnMessage:
    @pytest.mark.asyncio
    @patch("pint_bot.get_config")
    async def test_on_message_reacts_to_currency(self, mock_get_config):
        mock_get_config.return_value = {
            "REACT_TO_MESSAGES_MENTIONING_CURRENCY": True,
            "CURRENCY_NAME": "Pint",
            "REACTION_EMOJI": "🍺",
            "BOT_NAME": "Pint Bot"
        }

        mock_message = AsyncMock(spec=Message)
        mock_message.content = "I love pints!"
        mock_message.add_reaction = AsyncMock()
        
        with patch.object(type(bot), 'user', new_callable=PropertyMock) as mock_user:
            mock_user.return_value = MagicMock(id=999)
            mock_message.author = MagicMock(id=123)

            await on_message(mock_message)

        mock_message.add_reaction.assert_called_with("🍺")