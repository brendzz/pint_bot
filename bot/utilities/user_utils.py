import discord

async def get_display_name(client: discord.Client, user_id: str) -> str:
    try:
        user = await client.fetch_user(int(user_id))
        return user.display_name
    except discord.NotFound:
        return f"Unknown User ({user_id})"