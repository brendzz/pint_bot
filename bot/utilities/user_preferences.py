from bot import api_client
from bot.utilities.error_handling import handle_error

async def fetch_unicode_preference(interaction, user_id) -> bool:
    """Fetch the user's Unicode preference from the API."""
    try:
        response = api_client.get_unicode_preference(user_id)
        return response.get("use_unicode")
    except Exception as e:
        await handle_error(interaction, e, title="Error Fetching Unicode Preference")
        return False