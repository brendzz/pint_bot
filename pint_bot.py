import discord
from discord.ext import commands
from discord import app_commands
from fractions import Fraction
from pydantic import ValidationError
from bot_config import load_config
from currency_formatter import currency_formatter
from API.models import OweRequest, SettleRequest, SetUnicodePreferenceRequest
from error_messages import ERROR_MESSAGES
import api_client
from fraction_formatter import to_percentage
from send_messages import send_error_message, send_success_message, send_info_message, send_one_column_table_message, send_two_column_table_message
import requests
from fractions import Fraction

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot("!",intents=intents)

_config = None

def get_config():
    """
    Returns the bot configuration. Loads it from a file if not already loaded.
    """
    global _config
    if _config is None:
        _config = load_config()
    return _config

def format_error_message(text):
    """
    Formats the error message with values from config.
    """
    config = get_config()
    return text.format(
            CURRENCY=config["CURRENCY_NAME"],
            CURRENCY_PLURAL=config["CURRENCY_NAME_PLURAL"],
            MAX_DEBT=config["MAXIMUM_PER_DEBT"],
            SMALLEST_UNIT=config["SMALLEST_UNIT"],
            BOT_NAME=config["BOT_NAME"],
        )

def get_error_message(error_code):
    """
    Retrieves and formats an error message from ERROR_MESSAGES
    """
    error = ERROR_MESSAGES.get(error_code, ERROR_MESSAGES["UNKNOWN_ERROR"])
    return {
        "title": format_error_message(error["title"]),
        "description": format_error_message(error["description"])
    }

def parse_api_error(e):
    """
    Parses the API error response and returns a formatted error message.
    """
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
    """
    Handles errors and sends appropriate error messages.
    """
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

async def fetch_unicode_preference(interaction, user_id):
    try:
        return api_client.get_unicode_preference(user_id)
    except Exception as e:
        await handle_error(interaction, e, title="Error Fetching Unicode Preference")
        return None

@bot.event
async def on_ready():
    """
    Called when the bot is ready and connected to Discord.
    """
    print(f"Logged in as {bot.user} (ID: {bot.user.id})")
    print("------")
    config = get_config()
    register_commands(bot, config)
    await bot.tree.sync()
    print("Commands synced.")
    print("------")

@bot.event
async def on_message(message: discord.Message):
    """
    Called when a message is sent in a channel the bot can see.
    """
    config = get_config()
    
    # Ignore messages sent by the bot itself
    if message.author == bot.user:
        return

    # React to messages containing the currency name if the feature is enabled
    if config["REACT_TO_MESSAGES_MENTIONING_CURRENCY"]:
        if config["CURRENCY_NAME"].lower() in message.content.lower():
            try:
                await message.add_reaction(config["REACTION_EMOJI"])  # React with an emoji
            except discord.Forbidden:
                print("Bot does not have permission to add reactions.")
            except discord.HTTPException as e:
                print(f"Failed to add reaction: {e}")

    # Check if the bot is explicitly mentioned (not just replied to)
    if bot.user in message.mentions and not message.reference:
        embed = discord.Embed(
            title=f"Hello {message.author.display_name}!",
            description=f"I am {config["BOT_NAME"]}!\nI am currently set to manage the {config["CURRENCY_NAME"]} economy.\nUse '/help' to learn more.",
            color=discord.Color.yellow()
        )
        embed.set_footer(text=f"{config["BOT_NAME"]} - Your Local Friendly {config["CURRENCY_NAME"]} Economy Assistant.")
        embed.set_thumbnail(url=bot.user.avatar.url)
        await message.channel.send(embed=embed)

    # Process other commands (important to include this to avoid breaking command handling)
    await bot.process_commands(message)

def register_commands(bot, config: dict[str, any]):
    """
    Registers the bot commands with the Discord API.
    """
    @bot.tree.command(name="help", description="Get a list of available commands and their descriptions.")
    async def help_command(interaction: discord.Interaction):
        config = get_config()
        # Defer the interaction to avoid timeout
        await interaction.response.defer()
        # Define the list of commands and their descriptions
        commands = [
            {"name": "/help", "description": "Get a list of available commands and their descriptions."},
            {"name": "/owe", "description": f"Add a number of {config["CURRENCY_NAME_PLURAL"]} you owe someone."},
            {"name": f"/{config["GET_DEBTS_COMMAND"]}", "description": f"See your current {config["CURRENCY_NAME"]} debts."},
            {"name": f"/{config["GET_ALL_DEBTS_COMMAND"]}", "description": f"See everyone's total {config["CURRENCY_NAME"]} debts."},
            {"name": "/settle", "description": f"Settle {config["CURRENCY_NAME"]} debts with someone, starting with the oldest debts."},
            {"name": "/set_unicode_preference", "description": "Set your preference on whether to use unicode formatted fractions or not."},
            {"name": "/settings", "description": "See the current bot settings."},
        ]

        # Format the response
        help_message = f"I help to keep track of {config["CURRENCY_NAME"]} debts owed between users.\n__**{config["BOT_NAME"]} Commands:**__\n"
        for command in commands:
            help_message += f"**{command['name']}** - {command['description']}\n"

        help_message += "\n__**What can you use your Pints for?**__\n"
        for item in config["TRANSFERABLE_ITEMS"]:
            help_message += f"- {item}\n"

        # Send the help message
        await send_info_message(interaction,
                                title=f"{config["BOT_NAME"]} Help",
                                description=help_message)
        
    #Add a debt
    @bot.tree.command(name="owe", description=f"Add a number of {config['CURRENCY_NAME_PLURAL']} you owe someone.")
    @app_commands.describe(user="Who you owe", amount=f"How many {config['CURRENCY_NAME_PLURAL']} to owe", reason="Why you owe them (optional)")
    async def owe(interaction: discord.Interaction, user: discord.User, amount: str, *, reason: str = ""):
        config = get_config()
        debtor = interaction.user.id
        creditor = user.id

        # Defer the response to avoid timeout
        await interaction.response.defer()
        
        if debtor == creditor:
            await handle_error(interaction, error_code="CANNOT_OWE_SELF")
            return
        elif creditor == bot.user.id:
            await handle_error(interaction, error_code="CANNOT_OWE_BOT")
            return

        # Call the external API
        try:
            owe_request = OweRequest(
                debtor=debtor,
                creditor=creditor,
                amount=amount,
                reason=reason
            )
            payload = owe_request.model_dump()
            data = api_client.add_debt(payload)
        except Exception as e:
            await handle_error(interaction, e, title="Error Adding Debt")
            return
        
        use_unicode = await fetch_unicode_preference(interaction, interaction.user.id)
        
        await send_success_message(
                interaction,
                title=f"{config["CURRENCY_NAME"]} Debt Added - {config["CURRENCY_NAME"]} Economy Thriving",
                description=  f"Added {currency_formatter(data['amount'], config, use_unicode)} owed to {user.mention} for: *{data['reason']}* at {data['timestamp']}"
            )

    #See your own pint debts
    @bot.tree.command(name=config["GET_DEBTS_COMMAND"], description=f"See your current {config['CURRENCY_NAME']} debts.")
    @app_commands.describe(show_percentages="Display percentages of how much of the economy each person owes/is owed (Default: In Bot settings)")
    async def get_debts(interaction: discord.Interaction, show_percentages: bool = None):
        config = get_config()
        if show_percentages is None:
            show_percentages = config["SHOW_PERCENTAGES_DEFAULT"]

        user_id = str(interaction.user.id)
        # Defer the interaction to avoid timeout
        await interaction.response.defer()
        # Call the external API to fetch debts
        try:
            data = api_client.get_debts(user_id)
        except Exception as e:
            await handle_error(interaction, e, title=f"Error Fetching {config["CURRENCY_NAME"]} Debts")
            return
        
        # Check if the API returned a "message" field (no debts found)
        if "message" in data:
            await send_info_message(
                interaction,
                title=f"Looks like you're not currently contributing to the {config["CURRENCY_NAME"]} economy.",
                description=f"No debts found owed to or from this user. That's kind of cringe, get some {config["CURRENCY_NAME"]} debt bro."
            )
            return

        use_unicode = await fetch_unicode_preference(interaction, user_id)

        # Format the response
        lines = []

        # Debts owed by the user
        if data["owed_by_you"]:
            total_owed_by_you = Fraction(data['total_owed_by_you'])
            lines.append(f"__**{config["CURRENCY_NAME"]} YOU OWE:**__ {currency_formatter(total_owed_by_you, config, use_unicode).upper()}")
            for creditor_id, entries in data["owed_by_you"].items():
                try:
                    creditor = await bot.fetch_user(int(creditor_id))  # Fetch the creditor's username
                    creditor_name = creditor.display_name
                except discord.NotFound:
                    creditor_name = f"Unknown User ({creditor_id})"
                lines.append(f"\n**{creditor_name}**: {currency_formatter(sum(Fraction(entry['amount']) for entry in entries), config, use_unicode)}")
                for entry in entries:
                    amount = currency_formatter(entry["amount"], config, use_unicode)
                    if show_percentages:
                        amount+=f" ({to_percentage(entry['amount'],total_owed_by_you,config)}%)"
                    reason = entry["reason"]
                    timestamp = entry["timestamp"]
                    lines.append(f"- {amount} for *{reason}* on {timestamp}")

        # Debts owed to the user
        if data["owed_to_you"]:
            total_owed_to_you = Fraction(data['total_owed_to_you'])
            lines.append(f"\n__**{config["CURRENCY_NAME"]} OWED TO YOU:**__ {currency_formatter(total_owed_to_you, config, use_unicode).upper()}")
            for debtor_id, entries in data["owed_to_you"].items():
                try:
                    debtor = await bot.fetch_user(int(debtor_id))  # Fetch the debtor's username
                    debtor_name = debtor.display_name
                except discord.NotFound:
                    debtor_name = f"Unknown User ({debtor_id})"

                lines.append(f"\n**{debtor_name}**: {currency_formatter(sum(Fraction(entry['amount']) for entry in entries), config, use_unicode)}")
                for entry in entries:
                    amount = currency_formatter(entry["amount"], config, use_unicode)
                    if show_percentages:
                        amount+=f" ({to_percentage(entry['amount'],total_owed_to_you,config)}%)"
                    reason = entry["reason"]
                    timestamp = entry["timestamp"]
                    lines.append(f"- {amount} for *{reason}* on {timestamp}")

        # If no debts are found, return a message
        # Send the formatted response
        await send_info_message(
            interaction,
            title=f"Your {config["CURRENCY_NAME"]} debts *{interaction.user.display_name}*, thanks for participating in the {config["CURRENCY_NAME"]} economy!", 
            description="\n".join(lines)
            )
        # Send the formatted response

    #See everyone's pints
    @bot.tree.command(name=config["GET_ALL_DEBTS_COMMAND"], description=f"See everyone's total {config['CURRENCY_NAME']} debts.")
    @app_commands.describe(table_format="Display in table format (not recommended for mobile, Default: In Bot settings).", show_percentages="Display percentages of how much of the economy each person owes/is owed (Default: In Bot settings)")
    async def get_all_debts(interaction: discord.Interaction, table_format: bool = None, show_percentages: bool = None):
        config = get_config()
        if table_format is None:
            table_format = config["USE_TABLE_FORMAT_DEFAULT"]
        if show_percentages is None:
            show_percentages = config["SHOW_PERCENTAGES_DEFAULT"]

        # Defer the interaction to avoid timeout
        await interaction.response.defer()
        # Call the external API to fetch all debts
        try:
            data = api_client.get_all_debts()
        except Exception as e:
            await handle_error(interaction, e, title=f"Error Fetching {config["CURRENCY_NAME"]} Debts")
            return

        # Check if the API returned an empty response
        if not data:
            await handle_error(interaction, error_code="NO_DEBTS_IN_ECONOMY")
            return
        
        use_unicode = await fetch_unicode_preference(interaction, interaction.user.id)

        # Prepare the data for the table
        total_in_circulation = Fraction(data.pop("total_in_circulation", 0))
        table_data = []
        for user_id, totals in data.items():
            try:
                user = await bot.fetch_user(int(user_id))  # Fetch the user's username
                user_name = user.display_name
            except discord.NotFound:
                user_name = f"Unknown User ({user_id})"
            
            owes = currency_formatter(totals['owes'], config, use_unicode)
            is_owed = currency_formatter(totals['is_owed'], config, use_unicode)

            if show_percentages:
                owes += f" ({to_percentage(totals['owes'],total_in_circulation,config)}%)"
                is_owed += f" ({to_percentage(totals['is_owed'],total_in_circulation,config)}%)"

            table_data.append({
                "name": user_name,
                "Owes": owes,
                "Is Owed": is_owed
            })

        # Determine the economy health message
        economy_health_message = next(
            (health["message"] for health in config["ECONOMY_HEALTH_MESSAGES"] if total_in_circulation >= health["threshold"]),
            "The economy is in an unknown state"
        )

        # Call send_table_message to send the data as a table
        await send_two_column_table_message(
            interaction,
            title=f"{config["CURRENCY_NAME"]} Economy Overview",
            description=f"{economy_health_message}\n\n**Total {config["CURRENCY_NAME_PLURAL"]} in circulation: {currency_formatter(total_in_circulation, config, use_unicode)}**",
            data=table_data,
            table_format=table_format
        )

    @bot.tree.command(name="settle", description=f"Settle {config['CURRENCY_NAME']} debts with someone, starting with the oldest debts.")
    @app_commands.describe(user="Who you want to settle debts with", amount=f"How much to settle")
    async def settle(interaction: discord.Interaction, user: discord.User, amount: str):
        config = get_config()
        debtor = interaction.user.id
        creditor = user.id

        if debtor == creditor:
            await handle_error(interaction, error_code="CANNOT_SETTLE_SELF")
            return
        elif creditor == bot.user.id:
            await handle_error(interaction, error_code="CANNOT_SETTLE_BOT")
            return
        
    # Defer the response to avoid timeout
        await interaction.response.defer()

        # Call the external API to settle debts
        try:
            # Use the SettleRequest Pydantic model to validate the payload
            settle_request = SettleRequest(
                debtor=debtor,
                creditor=creditor,
                amount=amount
            )
            payload = settle_request.model_dump()

            # Send the request to the API
            data = api_client.settle_debt(payload)

        except Exception as e:
            await handle_error(interaction, e, title="Error Settling Debt")
            return

        use_unicode = await fetch_unicode_preference(interaction, interaction.user.id)

        # Send confirmation message
        settled_amount = currency_formatter(data["settled_amount"], config, use_unicode)
        remaining_amount = currency_formatter(data["remaining_amount"], config, use_unicode)
        await send_success_message(
            interaction,
            title="Debt Settled Successfully",
            description=  f"Settled {settled_amount} with {user.mention}. Remaining debt: {remaining_amount}."
        )

    @bot.tree.command(name="set_unicode_preference", description="Set your default preference for using Unicode fractions.")
    @app_commands.describe(use_unicode="Set to True to use Unicode fractions, False otherwise.")
    async def set_unicode_preference(interaction: discord.Interaction, use_unicode: bool):
        await interaction.response.defer()
        user_id = interaction.user.id  # Get the user's ID

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
        await send_success_message(
            interaction,
            title="Preference Updated",
            description=data["message"])

    @bot.tree.command(name="settings", description="View the current bot settings.")
    @app_commands.describe(table_format="Display in table format (not recommended for mobile, Default: In Bot Settings.).")
    async def settings_command(interaction: discord.Interaction, table_format: bool = None):
        config = get_config()
        if table_format is None:
            table_format = config["USE_TABLE_FORMAT_DEFAULT"]
        
        # Defer the interaction to avoid timeout
        await interaction.response.defer()

        # Prepare the bot settings data
        bot_settings_data=[]
        for key, value in get_config().items():
            bot_setting = {"Setting": key, "Value": value}
            bot_settings_data.append(bot_setting)
        
        # Send the bot settings as a one-column table
        await send_one_column_table_message(
            interaction,
            title=f"Current {config["BOT_NAME"]} Setting (Customizable)",
            description="Here are the current Bot settings:",
            data=bot_settings_data,
            table_format=table_format
        )

        # Prepare the API settings data
        api_settings_data = [
            {"Setting": "Maximum Debt Per Transaction", "Value": config["MAXIMUM_PER_DEBT"]},
            {"Setting": "Smallest Unit Allowed (Quantization)", "Value": config["SMALLEST_UNIT"]},
            {"Setting": "Maximum Debt Description Character Limit", "Value": config["MAXIMUM_DEBT_CHARACTER_LIMIT"]},
            {"Setting": "Enforce Quantization when Settling Debts", "Value": config["QUANTIZE_SETTLING_DEBTS"]}
        ]

        # Send the API settings as a one-column table
        await send_one_column_table_message(
            interaction,
            title=f"Current API Settings",
            description="Here are the current API settings:",
            data=api_settings_data,
            table_format=table_format
        )

def main():
    """
    Main function to run the bot.
    """
    bot.run(get_config()["BOT_TOKEN"])

if __name__ == "__main__":
    main()