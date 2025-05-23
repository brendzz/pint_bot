from unittest.mock import AsyncMock, patch, MagicMock
import pytest
import requests
from bot.utilities.error_handling import format_error_message, get_error_message, handle_error, parse_api_error

class TestFormatErrorMessage:
    def test_format_error_message(self):
        msg = format_error_message("You owe too much {CURRENCY}")
        assert msg == "You owe too much TestCoin"

class TestGetErrorMessage:
    def test_get_error_message_known(self):
        result = get_error_message("VALIDATION_ERROR")
        assert "TestBot" in result["title"]
        assert "Doesn't Like Your Data" in result["title"]

    def test_get_error_message_unknown(self):
        result = get_error_message("NON_EXISTENT_CODE")
        assert "Unknown Error" in result["title"]

class TestParseApiError:
    def test_parse_api_error_string_code(self):
        mock_response = MagicMock()
        mock_response.json.return_value = {"detail": "VALIDATION_ERROR: Invalid input"}
        exception = requests.exceptions.HTTPError(response=mock_response)

        with patch("bot.utilities.error_handling.get_error_message") as mock_get_error_message:
            mock_get_error_message.return_value = {"title": "Some Error", "description": "desc"}
            result = parse_api_error(exception)
            assert result["title"] == "Some Error"

    def test_parse_api_error_json_structure_unexpected(self):
        mock_response = MagicMock()
        mock_response.json.return_value = {"detail": {"not": "a string"}}
        exception = requests.exceptions.HTTPError(response=mock_response)

        with patch("bot.utilities.error_handling.get_error_message") as mock_get_error_message:
            mock_get_error_message.return_value = {"title": "Fallback", "description": "desc"}
            result = parse_api_error(exception)
            assert result["title"] == "Fallback"

    def test_parse_api_error_json_raises(self):
        mock_response = MagicMock()
        mock_response.json.side_effect = Exception("fail")
        exception = requests.exceptions.HTTPError(response=mock_response)

        with patch("bot.utilities.error_handling.get_error_message") as mock_get_error_message:
            mock_get_error_message.return_value = {"title": "Parser failed", "description": "desc"}
            result = parse_api_error(exception)
            assert result["title"] == "Parser failed"

class TestHandleError:
    @pytest.mark.asyncio
    async def test_handle_error_with_code(self):
        interaction = AsyncMock()
        with patch("bot.utilities.error_handling.get_error_message") as mock_get, \
            patch("bot.utilities.error_handling.send_messages.send_error_message", new_callable=AsyncMock) as mock_send:
            mock_get.return_value = {"title": "Error", "description": "desc"}
            await handle_error(interaction, error_code="SOME_CODE")
            mock_send.assert_awaited_once()
