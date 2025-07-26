from bot import api_client
import discord
from models.set_unicode_preference_request import SetUnicodePreferenceRequest
from bot.utilities.error_handling import handle_error
import bot.utilities.send_messages as send_messages
from bot.utilities.user_utils import get_display_name

async def handle_set_unicode_preference(interaction: discord.Interaction, use_unicode: bool):
    await interaction.response.defer()
    user_id = str(interaction.user.id)

    try:
        set_unicode_preference_request = SetUnicodePreferenceRequest(
            use_unicode=use_unicode
        )
        payload = set_unicode_preference_request.model_dump()

        data = api_client.set_unicode_preference(user_id, payload)
    except Exception as e:
        await handle_error(interaction, e, title="Error Updating Preference")
        return

    await send_messages.send_success_message(
        interaction,
        title="Preference Updated",
        description=data["message"])

async def handle_refresh_name(interaction: discord.Interaction):
    await interaction.response.defer()
    
    new_name = await get_display_name(interaction.client,interaction.user.id, True)
    await send_messages.send_success_message(
        interaction,
        title=f"Thanks {new_name} - Name Updated!",
        description=f"Updated my name cache with your name - *{new_name}*")