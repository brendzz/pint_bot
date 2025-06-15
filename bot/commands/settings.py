import discord
from bot import api_client
from bot import config
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
    {
        "Category": "General",
        "Settings": [
            {"Setting": "Bot Name", "Value": config.BOT_NAME},
            {"Setting": "Currency Name", "Value": config.CURRENCY_NAME},
            {"Setting": "Currency Name (Plural)", "Value": config.CURRENCY_NAME_PLURAL},
        ]
    },
    {
        "Category": "Commands",
        "Settings": [
            {"Setting": "Get Debts Command", "Value": config.GET_DEBTS_COMMAND},
            {"Setting": "Get All Debts Command", "Value": config.GET_ALL_DEBTS_COMMAND},
            {"Setting": "Get Debts With User Command", "Value": config.DEBTS_WITH_USER_COMMAND},
            {"Setting": "Roll Command", "Value": config.ROLL_COMMAND},
        ]
    },
    {
        "Category": "Display",
        "Settings": [
            {"Setting": "Use Decimal Output", "Value": config.USE_DECIMAL_OUTPUT},
            {"Setting": "Show Percentages by Default", "Value": config.SHOW_PERCENTAGES_DEFAULT},
            {"Setting": "Percentage Decimal Places", "Value": config.PERCENTAGE_DECIMAL_PLACES},
            {"Setting": "Show All Debt Details by Default", "Value": config.SHOW_DETAILS_DEFAULT},
            {"Setting": "Use Table Format by Default", "Value": config.USE_TABLE_FORMAT_DEFAULT},
            {"Setting": "Sort by who owes the most first by Default (API Setting)", "Value": config.SORT_OWES_FIRST}
        ]
    },
     {
        "Category": "Display - Conversion Currency",
        "Settings": [
            {"Setting": "Conversion Currency", "Value": config.CONVERSION_CURRENCY},
            {"Setting": "Show Conversion Currency by Default", "Value": config.SHOW_CONVERSION_CURRENCY_DEFAULT},
            {"Setting": "Conversion ratio of how many of units of debt currency = 1 unit of Conversion Currency", "Value": config.EXCHANGE_RATE_TO_CONVERSION_CURRENCY},
            {"Setting": "Show Conversino Currency Symble before amount by Default", "Value": config.CONVERSION_CURRENCY_SHOW_SYMBOL_BEFORE_AMOUNT}
        ]
    },
    {
        "Category": "Debt Rules - API Settings",
        "Settings": [
            {"Setting": "Maximum Debt Per Transaction", "Value": config.MAXIMUM_PER_DEBT},
            {"Setting": "Maximum Debt Description Character Limit", "Value": config.MAXIMUM_DEBT_CHARACTER_LIMIT},
            {"Setting": "Smallest Unit Allowed/Quantization", "Value": config.SMALLEST_UNIT},
            {"Setting": "Enforce Quantization when Owing Debts", "Value": config.QUANTIZE_OWING_DEBTS},
            {"Setting": "Enforce Quantization when Settling Debts", "Value": config.QUANTIZE_SETTLING_DEBTS}
        ]
    },
    {
        "Category": "Reactions",
        "Settings": [
            {"Setting": "React to Messages Mentioning Currency", "Value": config.REACT_TO_MESSAGES_MENTIONING_CURRENCY},
            {"Setting": "Reaction Emoji", "Value": config.REACTION_EMOJI},
            {"Setting": "Reaction Odds", "Value": config.REACTION_ODDS},
            {"Setting": "Reaction Emoji (Rare)", "Value": config.REACTION_EMOJI_RARE},
            {"Setting": "Reaction Odds (Rare)", "Value": config.REACTION_ODDS_RARE},
        ]
    },
    {
        "Category": "Fun",
        "Settings": [
            {"Setting": "Winning Number for Rolls", "Value": config.ROLL_WINNING_NUMBER}
        ]
    }
]
    formatted_data = []
    for category in bot_settings_data:
        if table_format:
           formatted_data.append({"Setting": f"**{category['Category']}**", "Value": "-"})
        else:
            formatted_data.append({"Setting": f"**__{category['Category']}__**", "Value": ""})
        for setting in category["Settings"]:
            formatted_data.append(setting)

        formatted_data.append({"Setting": " ", "Value": " "})
    
    if formatted_data and formatted_data[-1]["Setting"].strip() == "":
        formatted_data.pop()
        

    await send_messages.send_one_column_table_message(
        interaction,
        title=f"Current {config.BOT_NAME} Settings (Customizable)",
        description="Here are the current Bot settings:",
        data=formatted_data,
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
