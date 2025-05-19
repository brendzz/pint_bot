import discord
from bot import api_client, config
from bot.utilities.error_handling import handle_error
import bot.utilities.send_messages as send_messages
from models.set_unicode_preference_request import SetUnicodePreferenceRequest

async def handle_settings(interaction: discord.Interaction, table_format: bool = None):
    if table_format is None:
        table_format = config.USE_TABLE_FORMAT_DEFAULT

    # Defer the interaction to avoid timeout
    await interaction.response.defer()

    # Prepare the bot settings data
    bot_settings_data = [
        {"Setting": "Bot Name", "Value": config.BOT_NAME},
        {"Setting": "Currency Name", "Value": config.CURRENCY_NAME},
        {"Setting": "Currency Name (Plural)", "Value": config.CURRENCY_NAME_PLURAL},
        {"Setting": "Use Decimal Output", "Value": config.USE_DECIMAL_OUTPUT},
        {"Setting": "React to Messages Mentioning Currency", "Value": config.REACT_TO_MESSAGES_MENTIONING_CURRENCY},
        {"Setting": "Reaction Emoji", "Value": config.REACTION_EMOJI},
        {"Setting": "Reaction Odds", "Value": config.REACTION_ODDS},
        {"Setting": "Reaction Emoji (Rare)", "Value": config.REACTION_EMOJI_RARE},
        {"Setting": "Reaction Odds (Rare)", "Value": config.REACTION_ODDS_RARE},
        {"Setting": "Maximum Debt Per Transaction", "Value": config.MAXIMUM_PER_DEBT},
        {"Setting": "Smallest Unit Allowed (Quantization)", "Value": config.SMALLEST_UNIT},
        {"Setting": "Maximum Debt Description Character Limit", "Value": config.MAXIMUM_DEBT_CHARACTER_LIMIT},
        {"Setting": "Enforce Quantization when Settling Debts", "Value": config.QUANTIZE_SETTLING_DEBTS},
        {"Setting": "Show Percentages by Default", "Value": config.SHOW_PERCENTAGES_DEFAULT},
        {"Setting": "Show All Debt Details by Default", "Value": config.SHOW_DETAILS_DEFAULT},
        {"Setting": "Percentage Decimal Places", "Value": config.PERCENTAGE_DECIMAL_PLACES},
        {"Setting": "Get Debts Command", "Value": config.GET_DEBTS_COMMAND},
        {"Setting": "Get All Debts Command", "Value": config.GET_ALL_DEBTS_COMMAND},
        {"Setting": "Use Table Format Default", "Value": config.USE_TABLE_FORMAT_DEFAULT},
    ]

    # Send the bot settings as a one-column table
    await send_messages.send_one_column_table_message(
        interaction,
        title=f"Current {config.BOT_NAME} Settings (Customizable)",
        description="Here are the current Bot settings:",
        data=bot_settings_data,
        table_format=table_format
    )

async def handle_set_unicode_preference(interaction: discord.Interaction, use_unicode: bool):
    await interaction.response.defer()
    user_id = str(interaction.user.id)  # Get the user's ID

    # Call the external API to update the preference
    try:
        set_unicode_preference_request = SetUnicodePreferenceRequest(
            user_id=user_id,
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
