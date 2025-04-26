import discord
from discord.ext import commands
from discord import app_commands
from fractions import Fraction
from pydantic import ValidationError
#from constants import API_URL,BOT_NAME, BOT_TOKEN, CURRENCY_NAME, CURRENCY_NAME_PLURAL, GET_DEBTS_COMMAND, GET_ALL_DEBTS_COMMAND, MAXIMUM_DEBT_CHARACTER_LIMIT, MAXMIMUM_PER_DEBT, SMALLEST_UNIT
from currency_formatter import currency_formatter
from API.models import OweRequest, SettleRequest, SetUnicodePreferenceRequest
from error_messages import ERROR_MESSAGES

import api_client

from send_messages import send_error_message, send_success_message, send_info_message, send_table_message
import requests

from fractions import Fraction
from dotenv import load_dotenv
from os import environ

# Load environment variables
load_dotenv(".env")
BOT_NAME = environ.get("BOT_NAME", "Pint Bot")
BOT_TOKEN = environ.get("BOT_TOKEN")
API_URL = environ.get("API_URL", "http://127.0.0.1:8000")
CURRENCY_NAME = environ.get("CURRENCY_NAME","Pint")
CURRENCY_NAME_PLURAL = environ.get("CURRENCY_NAME_PLURAL","Pints")
USE_DECIMAL = environ.get("USE_DECIMAL", False)

load_dotenv("API/.env")
GET_DEBTS_COMMAND = environ.get("GET_DEBTS_COMMAND", "pints")
GET_ALL_DEBTS_COMMAND = environ.get("GET_ALL_DEBTS_COMMAND", "all_pints")
MAXMIMUM_PER_DEBT = int(environ.get("MAXMIMUM_PER_DEBT", "10"))  # Set a maximum debt limit
SMALLEST_UNIT = Fraction(environ.get("SMALLEST_UNIT", "1/6"))
MAXIMUM_DEBT_CHARACTER_LIMIT = int(environ.get("MAXIMUM_DEBT_CHARACTER_LIMIT", "200"))

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot("!",intents=intents)

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user} (ID: {bot.user.id})")
    print("------")
    await bot.tree.sync()

@bot.event
async def on_message(message: discord.Message):
    # Ignore messages sent by the bot itself
    if message.author == bot.user:
        return

    # Check if the bot is mentioned
    if bot.user.mentioned_in(message):
        embed = discord.Embed(
            title=f"Hello {message.author.display_name}!",
            description=f"I am {BOT_NAME}!\nI am currently set to manage the {CURRENCY_NAME} economy.\nUse '/help' to learn more.",
            color=discord.Color.yellow()
        )
        embed.set_footer(text=f"{BOT_NAME} - Your Local Friendly {CURRENCY_NAME} Economy Assistant.")
        embed.set_thumbnail(url=bot.user.avatar.url)
        await message.channel.send(embed=embed)
    
    # Process other commands (important to include this to avoid breaking command handling)
    await bot.process_commands(message)


@bot.tree.command(name="help", description="Get a list of available commands and their descriptions.")
async def help_command(interaction: discord.Interaction):
    await interaction.response.defer()
    # Define the list of commands and their descriptions
    commands = [
        {"name": "/help", "description": "Get a list of available commands and their descriptions."},
        {"name": "/owe", "description": f"Add a number of {CURRENCY_NAME_PLURAL} you owe someone."},
        {"name": f"/{GET_DEBTS_COMMAND}", "description": f"See your current {CURRENCY_NAME} debts."},
        {"name": f"/{GET_ALL_DEBTS_COMMAND}", "description": f"See everyone's total {CURRENCY_NAME} debts."},
        {"name": "/settle", "description": f"Settle {CURRENCY_NAME} debts with someone, starting with the oldest debts."},
        {"name": "/set_unicode_preference", "description": "Set your preference on whether to use unicode fromatted fractions or not."},
    ]

    # Format the response
    help_message = f"I help to keep track of {CURRENCY_NAME} debts owed between users.\n__**{BOT_NAME} Commands:**__\n"
    for command in commands:
        help_message += f"**{command['name']}** - {command['description']}\n"

    # Send the help message
    await send_info_message(interaction,
                            title=f"{BOT_NAME} Help",
                            description=help_message)

def handle_api_error(e):
    try:
        # Access the response JSON from the HTTPError object
        response_json = e.response.json()  # Correct way to get the JSON response

        # Extract the "detail" field from the response
        error_details = response_json.get("detail", "UNKNOWN_ERROR")
        if isinstance(error_details, str):
            error_code = error_details.split(":")[0]  # Extract the error code

            # Get the error message from the ERROR_MESSAGES dictionary
            error_message = ERROR_MESSAGES.get(error_code, ERROR_MESSAGES["UNKNOWN_ERROR"])

            # Return the formatted error message
            return {
                "title": error_message["title"],
                "description": error_message["description"].format(
                    currency=CURRENCY_NAME,
                    currency_plural=CURRENCY_NAME_PLURAL,
                    max_debt=MAXMIMUM_PER_DEBT,
                    smallest_unit=SMALLEST_UNIT
                )
            }

        # Fallback for unexpected error formats
        return {
            "title": "Error",
            "description": "An unexpected error occurred."
        }
    except Exception as ex:
        return {
            "title": "Error",
            "description": "An unknown error occurred."
        }
    
#Add a debt
@bot.tree.command(name="owe", description=f"Add a number of {CURRENCY_NAME} you owe someone.")
@app_commands.describe(user="Who you owe", amount=f"How many {CURRENCY_NAME_PLURAL}", reason="Why you owe them (optional)")
async def owe(interaction: discord.Interaction, user: discord.User, amount: str, *, reason: str = ""):
    debtor = interaction.user.id
    creditor = user.id

    if debtor == creditor:
        await send_error_message(interaction,
            title=f"Illegal {CURRENCY_NAME} Activities Detected",
            description=f"You can't owe yourself {CURRENCY_NAME_PLURAL}, that would be too confusing sorry. The {CURRENCY_NAME} economy is a complex system, and we don't want to break it.")
        return
    elif creditor == bot.user.id:
        await send_info_message(
            interaction,
            title=f"{BOT_NAME} thanks you for the offer!",
            description=f"{BOT_NAME} already has plenty of {CURRENCY_NAME_PLURAL}, but thanks for the generous offer!"
        )
        return
    
     # Defer the response to avoid timeout
    await interaction.response.defer()
    
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

    except requests.exceptions.HTTPError as e:
        error_message= handle_api_error(e)
        await send_error_message(
            interaction,
            title=error_message["title"],
            description=error_message["description"]
        )
        return
    
    except ValidationError as e:
        await send_error_message(
            interaction,
            title=f"{BOT_NAME} doesn't like your data",
            description=f"Looks like you've got some invalid data there buddy - we've got {MAXIMUM_DEBT_CHARACTER_LIMIT} character limits around these parts."
        )
        return
    try:
        use_unicode = api_client.get_unicode_preference(interaction.user.id)
    except requests.exceptions.RequestException as e:
        await send_error_message(
            interaction,
            title=f"Unicode fetching Error.",
            description=f"Error fetching your unicode preference: {e}"
        )
        return
    await send_success_message(
            interaction,
            title=f"{CURRENCY_NAME} Debt Added - {CURRENCY_NAME} Economy Thriving",
            description=  f"Added {currency_formatter(data['amount'],use_unicode, CURRENCY_NAME, CURRENCY_NAME_PLURAL, USE_DECIMAL)} owed to {user.mention} for: *{data['reason']}* at {data['timestamp']}"
        )

#See your own pint debts
@bot.tree.command(name=f"{GET_DEBTS_COMMAND}", description=f"See your current {CURRENCY_NAME} debts.")
@app_commands.describe(use_unicode="Use Unicode fractions (default: based on your preference).")
async def get_debts(interaction: discord.Interaction, use_unicode: bool = None):
    
    user_id = str(interaction.user.id)
    # Defer the interaction to avoid timeout
    await interaction.response.defer()
    # Call the external API to fetch debts
    try:
        data = api_client.get_debts(user_id)
    except requests.exceptions.RequestException as e:
        await send_error_message(
            interaction,
            title=f"The {CURRENCY_NAME} economy is broken!",
            description=f"Error fetching your {CURRENCY_NAME} debts: {e}"
        )
        return
    
    # Check if the API returned a "message" field (no debts found)
    if "message" in data:
        await send_info_message(
            interaction,
            title=f"Looks like you're not currently contributing to the {CURRENCY_NAME} economy.",
            description=f"No debts found owed to or from this user. That's kind of cringe, get some {CURRENCY_NAME} debt bro."
        )
        return

   
    if use_unicode is None:
        try:
            use_unicode = api_client.get_unicode_preference(user_id)
        except requests.exceptions.RequestException as e:
            await send_error_message(
                interaction,
                title=f"Unicode fetching Error.",
                description=f"Error fetching your unicode preference: {e}"
            )
            return

    # Format the response
    lines = []

    # Debts owed by the user
    if data["owed_by_you"]:
        lines.append(f"__**{CURRENCY_NAME} YOU OWE:**__ {currency_formatter(data["total_owed_by_you"], use_unicode,CURRENCY_NAME, CURRENCY_NAME_PLURAL, USE_DECIMAL).upper()}")
        for creditor_id, entries in data["owed_by_you"].items():
            try:
                creditor = await bot.fetch_user(int(creditor_id))  # Fetch the creditor's username
                creditor_name = creditor.display_name
            except discord.NotFound:
                creditor_name = f"Unknown User ({creditor_id})"
            lines.append(f"\n**{creditor_name}**: {currency_formatter(sum(Fraction(entry["amount"]) for entry in entries), use_unicode, CURRENCY_NAME, CURRENCY_NAME_PLURAL, USE_DECIMAL)}")
            for entry in entries:
                amount = currency_formatter(entry["amount"], use_unicode, CURRENCY_NAME, CURRENCY_NAME_PLURAL, USE_DECIMAL)
                reason = entry["reason"]
                timestamp = entry["timestamp"]
                lines.append(f"- {amount} for *{reason}* on {timestamp}")

    # Debts owed to the user
    if data["owed_to_you"]:
        lines.append(f"\n__**{CURRENCY_NAME} OWED TO YOU:**__ {currency_formatter(data["total_owed_to_you"], use_unicode, CURRENCY_NAME, CURRENCY_NAME_PLURAL, USE_DECIMAL).upper()}")
        for debtor_id, entries in data["owed_to_you"].items():
            try:
                debtor = await bot.fetch_user(int(debtor_id))  # Fetch the debtor's username
                debtor_name = debtor.display_name
            except discord.NotFound:
                debtor_name = f"Unknown User ({debtor_id})"
            
            lines.append(f"\n**{debtor_name}**: {currency_formatter(sum(Fraction(entry["amount"], use_unicode, CURRENCY_NAME, CURRENCY_NAME_PLURAL, USE_DECIMAL) for entry in entries))}")
            for entry in entries:
                amount = currency_formatter(entry["amount"], use_unicode, CURRENCY_NAME, CURRENCY_NAME_PLURAL, USE_DECIMAL)
                reason = entry["reason"]
                timestamp = entry["timestamp"]
                lines.append(f"- {amount} for *{reason}* on {timestamp}")

    # If no debts are found, return a message
    # Send the formatted response
    await send_info_message(
        interaction,
        title=f"Your {CURRENCY_NAME} debts *{interaction.user.display_name}*, thanks for participating in the {CURRENCY_NAME} economy!", 
        description="\n".join(lines)
        )
    # Send the formatted response


#See everyone's pints
@bot.tree.command(name=f"{GET_ALL_DEBTS_COMMAND}", description=f"See everyone's total {CURRENCY_NAME} debts.")
async def get_all_debts(interaction: discord.Interaction, use_unicode: bool = None):
    # Defer the interaction to avoid timeout
    await interaction.response.defer()
    # Call the external API to fetch all debts
    try:
        data = api_client.get_all_debts()
    except requests.exceptions.RequestException as e:
        error_message= handle_api_error(e)
        await send_error_message(
            interaction,
            title=error_message["title"],
            description=error_message["description"]
        )
        return

    # Check if the API returned an empty response
    if not data:
        await send_error_message(interaction,
                                 title=f"No {CURRENCY_NAME} debts found.",
                                 description=f"The {CURRENCY_NAME} economy is in shambles! Financial Crash!")
        return
    
    if use_unicode is None:
        try:
            use_unicode = api_client.get_unicode_preference(interaction.user.id)
        except requests.exceptions.RequestException as e:
            await send_error_message(
                interaction,
                title=f"Unicode fetching Error.",
                description=f"Error fetching your unicode preference: {e}"
            )
            return
   # Prepare the data for the table
    table_data = []
    for user_id, totals in data.items():
        try:
            user = await bot.fetch_user(int(user_id))  # Fetch the user's username
            user_name = user.display_name
        except discord.NotFound:
            user_name = f"Unknown User ({user_id})"

        table_data.append({
            "name": user_name,
            "Owes": currency_formatter(totals["owes"], use_unicode, CURRENCY_NAME, CURRENCY_NAME_PLURAL, USE_DECIMAL),
            "Is Owed": currency_formatter(totals["is_owed"], use_unicode, CURRENCY_NAME, CURRENCY_NAME_PLURAL, USE_DECIMAL)
        })

    # Call send_table_message to send the data as a table
    await send_table_message(
        interaction,
        title=f"{CURRENCY_NAME} Economy Overview",
        description=f"Current state of the {CURRENCY_NAME} economy:",
        data=table_data
    )

@bot.tree.command(name="settle", description=f"Settle {CURRENCY_NAME} debts with someone, starting with the oldest debts.")
@app_commands.describe(user="Who you want to settle debts with", amount=f"How many {CURRENCY_NAME} to settle")
async def settle(interaction: discord.Interaction, user: discord.User, amount: str):
    debtor = interaction.user.id
    creditor = user.id

    if debtor == creditor:
        await send_error_message(
            interaction,
            title=f"Illegal {CURRENCY_NAME} Activities Detected",
            description=f"You can't have {CURRENCY_NAME} debts with yourself. You have the power to buy yourself a {CURRENCY_NAME} without the need for this bot.")
        return
    elif creditor == bot.user.id:
        await send_error_message(
            interaction,
            title=f"{CURRENCY_NAME} Economy Financial Regulations Violation",
            description=f"Due to {CURRENCY_NAME} Economy Financial Regulations, it is illegal to settle pints with {BOT_NAME} as it would be conflict of interest for {BOT_NAME} to run the {CURRENCY_NAME} economy and also participate in it.")
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

    except requests.exceptions.HTTPError as e:
        # Extract the error details from the response
        error_message = handle_api_error(e)

        await send_error_message(
            interaction,
            title=error_message["title"],
            description=error_message["description"]
        )
        return
    except ValidationError as e:
        await send_error_message(
            interaction,
            title="Invalid Data",
            description="The data provided is invalid. Please check your input and try again."
        )
        return
    except requests.exceptions.RequestException as e:
        await send_error_message(
            interaction,
            title="Request Error",
            description=f"An error occurred while processing your request: {e}"
        )
        return

    try:
        use_unicode = api_client.get_unicode_preference(interaction.user.id)
    except requests.exceptions.RequestException as e:
        await send_error_message(
            interaction,
            title=f"Unicode fetching Error.",
            description=f"Error fetching your unicode preference: {e}"
        )
        return

    # Send confirmation message
    settled_amount = currency_formatter(data["settled_amount"], use_unicode, CURRENCY_NAME, CURRENCY_NAME_PLURAL, USE_DECIMAL)
    remaining_amount = currency_formatter(data["remaining_amount"], use_unicode, CURRENCY_NAME, CURRENCY_NAME_PLURAL, USE_DECIMAL)
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
    except requests.exceptions.RequestException as e:
        await send_error_message(
            interaction,
            title="Error Updating Preference",
            description=f"An error occurred while updating your preference: {e}"
        )
        return
    except Exception as e:
        # Catch any other exceptions
        await send_error_message(
            interaction,
            title="Unexpected Error",
            description=f"An unexpected error occurred: {e}"
        )
        return
    # Provide feedback to the user
    await send_success_message(
        interaction,
        title="Preference Updated",
        description=data["message"])

bot.run(BOT_TOKEN)