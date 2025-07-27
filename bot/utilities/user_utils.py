import discord

_user_display_name_cache = {}

async def get_display_name(client: discord.Client, user_id: str, force_refresh: bool = False) -> str:
    if not force_refresh and user_id in _user_display_name_cache:
        return _user_display_name_cache[user_id]
    try:
        user = await client.fetch_user(int(user_id))
        display_name = user.display_name
    except discord.NotFound:
        display_name = f"Unknown User ({user_id})"
    _user_display_name_cache[user_id] = display_name
    return display_name