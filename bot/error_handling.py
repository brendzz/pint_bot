import discord 
from pydantic import ValidationError
import requests
import bot.config as config
from bot.error_messages import ERROR_MESSAGES
from bot.send_messages import send_error_message

def format_error_message(error_message: str):
    """Formats the error message with values from config."""
    return error_message.format(
            CURRENCY=config.CURRENCY_NAME,
            CURRENCY_PLURAL=config.CURRENCY_NAME_PLURAL,
            MAX_DEBT=config.MAXIMUM_PER_DEBT,
            SMALLEST_UNIT=config.SMALLEST_UNIT,
            BOT_NAME=config.BOT_NAME,
        )

def get_error_message(error_code: str):
    """Retrieves and formats an error message from ERROR_MESSAGES."""
    error = ERROR_MESSAGES.get(error_code, ERROR_MESSAGES["UNKNOWN_ERROR"])
    return {
        "title": format_error_message(error["title"]),
        "description": format_error_message(error["description"])
    }

def parse_api_error(e: requests.exceptions.HTTPError):
    """Parses the API error response and returns a formatted error message."""
    try:
        # Extract the "detail" field from the response
        error_details = e.response.json().get("detail", "UNKNOWN_ERROR")
        if isinstance(error_details, str):
            error_code = error_details.split(":")[0]

            # Return the formatted error message
            return get_error_message(error_code)

        # Fallback if "detail" is not a string
        return get_error_message("UNKNOWN_API_ERROR")
    except Exception:
        return get_error_message("ERROR_PARSING_ERROR")

async def handle_error(interaction: discord.Interaction, error=None, error_code: str=None, title: str=None):
    """Handles errors and sends appropriate error messages."""
    if error_code:
        error_message = get_error_message(error_code)
    elif isinstance(error, requests.exceptions.HTTPError):
        error_message = parse_api_error(error)
    elif isinstance(error, ValidationError):
        error_message = get_error_message("VALIDATION_ERROR")
    elif isinstance(error, requests.exceptions.RequestException):
        error_message = get_error_message("REQUEST_ERROR")
    else:
        error_message = get_error_message("UNKNOWN_ERROR")

    if title:
        error_message["title"] = format_error_message(title)

    await send_error_message(interaction, error_message["title"], error_message["description"])
