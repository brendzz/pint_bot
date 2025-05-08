from fractions import Fraction
import discord 
from discord import app_commands
from API.models import OweRequest, SetUnicodePreferenceRequest, SettleRequest
import api_client
from error_handling import handle_error
from formatter import currency_formatter, to_percentage
from send_messages import send_info_message, send_one_column_table_message, send_success_message, send_two_column_table_message

async def fetch_unicode_preference(interaction, user_id) -> bool:
    """Fetch the user's Unicode preference from the API."""
    try:
        response = api_client.get_unicode_preference(user_id)
        return response.get("use_unicode")
    except Exception as e:
        await handle_error(interaction, e, title="Error Fetching Unicode Preference")
        return False

def register_commands(bot, config: dict[str, any]):
    """Registers the bot commands with the Discord API."""
    @bot.tree.command(name="help", description="Get a list of available commands and their descriptions.")
    async def help_command(interaction: discord.Interaction):
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
                description= f"Added {currency_formatter(data['amount'], config, use_unicode)} owed to {user.mention} for: *{data['reason']}* at {data['timestamp']}"
            )

    #See your own pint debts
    @bot.tree.command(name=config["GET_DEBTS_COMMAND"], description=f"See your current {config['CURRENCY_NAME']} debts.")
    @app_commands.describe(show_percentages="Display percentages of how much of the economy each person owes/is owed (Default: In Bot settings)")
    async def get_debts(interaction: discord.Interaction, show_percentages: bool = None):
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
                        amount+=f" {to_percentage(entry['amount'],total_owed_by_you,config)}"
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
                        amount+=f" {to_percentage(entry['amount'],total_owed_to_you,config)}"
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
        if data == {'total_in_circulation': '0'}:
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
                owes += f" {to_percentage(totals['owes'],total_in_circulation,config)}"
                is_owed += f" {to_percentage(totals['is_owed'],total_in_circulation,config)}"

            table_data.append({
                "name": user_name,
                "Owes": owes,
                "Is Owed": is_owed
            })

        # Determine the economy health message
        economy_health_message = (
            max(
                (
                    health
                    for health in config["ECONOMY_HEALTH_MESSAGES"]
                    if total_in_circulation >= health["threshold"]
                ),
                key=lambda h: h["threshold"],
                default={"message": "The economy is in an unknown state"}
            )["message"]
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
    @app_commands.describe(user="Who you want to settle debts with", amount=f"How many {config['CURRENCY_NAME_PLURAL']} to settle")
    async def settle(interaction: discord.Interaction, user: discord.User, amount: str):
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
            description= f"Settled {settled_amount} with {user.mention}. Remaining debt: {remaining_amount}."
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
        if table_format is None:
            table_format = config["USE_TABLE_FORMAT_DEFAULT"]
        
        # Defer the interaction to avoid timeout
        await interaction.response.defer()

        # Prepare the bot settings data
        bot_settings_data=[]
        for key, value in config.items():
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
            title=f"Current {config["BOT_NAME"]} API Settings",
            description="Here are the current API settings:",
            data=api_settings_data,
            table_format=table_format
        )