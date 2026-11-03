"""Handlers for user preferences. Platform-agnostic."""
from bot import api_client
from models.set_unicode_preference_request import SetUnicodePreferenceRequest
from bot.platform.context import CommandContext
from bot.utilities.error_handling import handle_error

async def handle_set_unicode_preference(ctx: CommandContext, use_unicode: bool):
    await ctx.defer()
    user_id = ctx.user_id

    try:
        set_unicode_preference_request = SetUnicodePreferenceRequest(
            use_unicode=use_unicode
        )
        payload = set_unicode_preference_request.model_dump()

        data = await api_client.set_unicode_preference(user_id, payload)
    except Exception as e:
        await handle_error(ctx, e, title="Error Updating Preference")
        return

    await ctx.messenger.success(
        ctx,
        title="Preference Updated",
        description=data["message"])

async def handle_refresh_name(ctx: CommandContext):
    await ctx.defer()

    new_name = await ctx.display_name(ctx.user_id, force_refresh=True)
    await ctx.messenger.success(
        ctx,
        title=f"Thanks {new_name} - Name Updated!",
        description=f"Updated my name cache with your name - *{new_name}*")
