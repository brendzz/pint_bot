from bot import api_client
import discord
from models.set_unicode_preference_request import SetUnicodePreferenceRequest
from bot.utilities.error_handling import handle_error
import bot.utilities.send_messages as send_messages

async def handle_set_unicode_preference(interaction: discord.Interaction, use_unicode: bool):
    await interaction.response.defer()
    user_id = str(interaction.user.id)  # Get the user's ID

    # Call the external API to update the preference
    try:
        set_unicode_preference_request = SetUnicodePreferenceRequest(
            use_unicode=use_unicode
        )
        payload = set_unicode_preference_request.model_dump()

        # Send the request to the API
        data = api_client.set_unicode_preference(payload)
    except Exception as e:
        await handle_error(interaction, e, title="Error Updating Preference")
        return
    # Provide feedback to the user
    await send_messages.send_success_message(
        interaction,
        title="Preference Updated",
        description=data["message"])
