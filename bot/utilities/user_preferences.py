"""Fetch the per-user Unicode fraction preference."""
import logging
from bot import api_client

logger = logging.getLogger(__name__)

async def fetch_unicode_preference(ctx, user_id: str) -> bool:
    """Fetch the user's Unicode preference from the API.

    The preference only affects display formatting, so on failure we
    silently fall back to the default (False) rather than showing an
    error message and then continuing to send a second message.
    """
    try:
        return bool(await api_client.get_unicode_preference(str(user_id)))
    except Exception as e:
        logger.warning("Failed to fetch Unicode preference for user %s: %s", user_id, e)
        return False
