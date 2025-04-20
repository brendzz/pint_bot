import discord
from discord.ext import commands
from discord import app_commands
from fractions import Fraction
from pydantic import ValidationError
from os import environ
from dotenv import load_dotenv
from currency_formatter import currency_formatter
from models import OweRequest
import api_client

from send_messages import send_error_message, send_success_message, send_info_message, send_table_message
import requests

intents = discord.Intents.default()
intents.message_content = True

load_dotenv(".env")
BOT_TOKEN = environ.get("BOT_TOKEN")
OWNER_ID = environ.get("OWNER_ID")

load_dotenv("API/.env")
CURRENCY_NAME = environ.get("CURRENCY_NAME")
GET_DEBTS_COMMAND = environ.get("GET_DEBTS_COMMAND")
GET_ALL_DEBTS_COMMAND = environ.get("GET_ALL_DEBTS_COMMAND")

bot = commands.Bot("!",intents=intents)

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user} (ID: {bot.user.id})")
    print("------")
    await bot.tree.sync()

@bot.tree.command(name='sync', description='Sync commands globally or for your personal DMs.')
@app_commands.describe(guild_id="The ID of the guild to sync commands for (optional). Leave blank for global sync.")
async def sync(interaction: discord.Interaction, guild_id: str = None):
    if interaction.user.id != int(OWNER_ID):
        await interaction.response.send_message('You must be the owner to use this command!', ephemeral=True)
        return

    try:
        if guild_id:
            # Sync commands for a specific guild
            guild = discord.Object(id=int(guild_id))
            await bot.tree.sync(guild=guild)
            await interaction.response.send_message(f"Commands synced for guild ID: {guild_id}")
        else:
            # Sync commands globally (includes DMs)
            await bot.tree.sync()
            await interaction.response.send_message("Commands synced globally (including DMs).")
    except Exception as e:
        await interaction.response.send_message(f"Failed to sync commands: {e}", ephemeral=True)

@bot.event
async def on_message(message: discord.Message):
    # Ignore messages sent by the bot itself
    if message.author == bot.user:
        return

    # Check if the bot is mentioned
    if bot.user.mentioned_in(message):
        embed = discord.Embed(
            title=f"Hello {message.author.display_name}!",
            description=f"I am Pint Bot!\nI am currently set to manage the {CURRENCY_NAME} economy.\nUse '/help' to learn more.",
            color=discord.Color.yellow()
        )
        embed.set_footer(text=f"Pint Bot - Your Local Friendly {CURRENCY_NAME} Economy Assistant.")
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
        {"name": "/owe", "description": f"Add a number of {CURRENCY_NAME}s you owe someone."},
        {"name": f"/{GET_DEBTS_COMMAND}", "description": f"See your current {CURRENCY_NAME} debts."},
        {"name": f"/{GET_ALL_DEBTS_COMMAND}", "description": f"See everyone's total {CURRENCY_NAME} debts."},
        {"name": "/settle", "description": f"Settle {CURRENCY_NAME} debts with someone, starting with the oldest debts."},
        {"name": "/sync", "description": "TEMPORARY COMMAND - Sync commands globally or for your personal DMs."},
    ]

    # Format the response
    help_message = f"I help to keep track of {CURRENCY_NAME} debts owed between users.\n__**Pint Bot Commands:**__\n"
    for command in commands:
        help_message += f"**{command['name']}** - {command['description']}\n"

    # Send the help message
    await send_info_message(interaction,
                            title="Pint Bot Help",
                            description=help_message)

def handle_api_error(e):
    try:
        error_details = e.response.json().get("detail", "An unknown error occurred.")
        if isinstance(error_details, list):
            return "; ".join([err["msg"] for err in error_details])
        return error_details
    except Exception:
        return "An unknown error occurred."

#Add a pint debt
@bot.tree.command(name="owe", description=f"Add a number of {CURRENCY_NAME} you owe someone.")
@app_commands.describe(user="Who you owe", pint_number=f"How many {CURRENCY_NAME}s", reason="Why you owe them (optional)")
async def owe(interaction: discord.Interaction, user: discord.User, pint_number: str, *, reason: str = ""):
    debtor = interaction.user.id
    creditor = user.id
    # Defer the interaction to avoid timeout
    await interaction.response.defer()

    if debtor == creditor:
        await send_error_message(interaction,
            title=f"Illegal {CURRENCY_NAME} Activities Detected",
            description=f"You can't owe yourself {CURRENCY_NAME}s, that would be too confusing sorry. The {CURRENCY_NAME} economy is a complex system, and we don't want to break it.")
        return
    elif creditor == bot.user.id:
        await send_info_message(
            interaction,
            title="Pint Bot thanks you for the offer!",
            description=f"Pint Bot already has plenty of {CURRENCY_NAME}s, but thanks for the generous offer!"
        )
        return
    
     # Defer the response to avoid timeout
    await interaction.response.defer()
    # Call the external API
    try:
        owe_request = OweRequest(
            debtor=debtor,
            creditor=creditor,
            pint_number=pint_number,
            reason=reason
        )
        payload = owe_request.model_dump()
        data = api_client.add_debt(payload)

    except requests.exceptions.HTTPError as e:
        error_message= handle_api_error(e)
        await send_error_message(
            interaction,
            title="Error Settling Debts!",
            description=f"{error_message}"
        )
        return
    
    except ValidationError as e:
        await send_error_message(
            interaction,
            title="Pint Bot doesn't like your data",
            description="Looks like you've got some invalid data there buddy - we've got 200 character limits around these parts."
        )
        return
    await send_success_message(
            interaction,
            title=f"{CURRENCY_NAME} Debt Added - {CURRENCY_NAME} Economy Thriving",
            description=  f"Added {currency_formatter(data['amount'])} owed to {user.mention} for: *{data['reason']}* at {data['timestamp']}"
        )

#See your own pint debts
@bot.tree.command(name=f"{GET_DEBTS_COMMAND}", description=f"See your current {CURRENCY_NAME} debts.")
@app_commands.describe(use_unicode="Use Unicode fractions (default: based on your preference).")
async def pints(interaction: discord.Interaction, use_unicode: bool = None):
    
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
            description=data["message"]
        )
        return

    # Format the response
    lines = []
    use_unicode = use_unicode if use_unicode is not None else data["use_unicode"]

    # Debts owed by the user
    if data["owed_by_you"]:
        lines.append(f"__**{CURRENCY_NAME} YOU OWE:**__ {currency_formatter(data["total_owed_by_you"], use_unicode).upper()}")
        for creditor_id, entries in data["owed_by_you"].items():
            try:
                creditor = await bot.fetch_user(int(creditor_id))  # Fetch the creditor's username
                creditor_name = creditor.display_name
            except discord.NotFound:
                creditor_name = f"Unknown User ({creditor_id})"
            lines.append(f"\n**{creditor_name}**: {currency_formatter(sum(Fraction(entry["amount"]) for entry in entries), use_unicode)}")
            for entry in entries:
                amount = currency_formatter(entry["amount"], use_unicode)
                reason = entry["reason"]
                timestamp = entry["timestamp"]
                lines.append(f"- {amount} for *{reason}* on {timestamp}")

    # Debts owed to the user
    if data["owed_to_you"]:
        lines.append(f"\n__**{CURRENCY_NAME} OWED TO YOU:**__ {currency_formatter(data["total_owed_to_you"], use_unicode).upper()}")
        for debtor_id, entries in data["owed_to_you"].items():
            try:
                debtor = await bot.fetch_user(int(debtor_id))  # Fetch the debtor's username
                debtor_name = debtor.display_name
            except discord.NotFound:
                debtor_name = f"Unknown User ({debtor_id})"
            
            lines.append(f"\n**{debtor_name}**: {currency_formatter(sum(Fraction(entry["amount"], use_unicode) for entry in entries))}")
            for entry in entries:
                amount = currency_formatter(entry["amount"], use_unicode)
                reason = entry["reason"]
                timestamp = entry["timestamp"]
                lines.append(f"- {amount} for *{reason}* on {timestamp}")

    # Send the formatted response
    await send_info_message(
        interaction,
        title=f"Your {CURRENCY_NAME} debts *{interaction.user.display_name}*, thanks for participating in the {CURRENCY_NAME} economy!", 
        description="\n".join(lines)
        )
    # Send the formatted response


#See everyone's pints
@bot.tree.command(name=f"{GET_ALL_DEBTS_COMMAND}", description=f"See everyone's total {CURRENCY_NAME} debts.")
async def allpints(interaction: discord.Interaction, use_unicode: bool = True):
    # Defer the interaction to avoid timeout
    await interaction.response.defer()
    # Call the external API to fetch all debts
    try:
        data = api_client.get_all_debts()
    except requests.exceptions.RequestException as e:
        error_message= handle_api_error(e)
        await send_error_message(
            interaction,
            title="Error seeing everyone's pint!",
            description=f"{error_message}"
        )
        return

    # Check if the API returned an empty response
    if not data:
        await send_error_message(interaction,
                                 title=f"No {CURRENCY_NAME} debts found.",
                                 description=f"The {CURRENCY_NAME} economy is in shambles! Financial Crash!")
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
            "Owes": currency_formatter(totals["owes"], use_unicode),
            "Is Owed": currency_formatter(totals["is_owed"], use_unicode)
        })

    # Call send_table_message to send the data as a table
    await send_table_message(
        interaction,
        title=f"{CURRENCY_NAME} Economy Overview",
        description=f"Current state of the {CURRENCY_NAME} economy:",
        data=table_data
    )

@bot.tree.command(name="settle", description=f"Settle {CURRENCY_NAME} debts with someone, starting with the oldest debts.")
@app_commands.describe(user="Who you want to settle debts with", pint_number=f"How many {CURRENCY_NAME} to settle")
async def settle(interaction: discord.Interaction, user: discord.User, pint_number: str):
    debtor = interaction.user.id
    creditor = user.id

    if debtor == creditor:
        await send_error_message(
            interaction,
            title="Illegal {CURRENCY_NAME} Activities Detected",
            description=f"You can't have {CURRENCY_NAME} debts with yourself. You have the power to buy yourself a {CURRENCY_NAME} without the need for this bot.")
        return
    elif creditor == bot.user.id:
        await send_error_message(
            interaction,
            title="{CURRENCY_NAME} Economy Financial Regulations Violation",
            description=f"Due to {CURRENCY_NAME} Economy Financial Regulations, it is illegal to settle pints with Pint Bot as it would be conflict of interest for Pint Bot to run the {CURRENCY_NAME} economy and also participate in it.")
        return
    
    # Defer the response to avoid timeout
    await interaction.response.defer()

    # Call the external API to settle debts
    try:
        payload = {"debtor": debtor, "creditor": creditor, "pint_number": pint_number}
        response = requests.post(f"{API_URL}/settle", json=payload)
        response.raise_for_status()
        data = response.json()
    except requests.exceptions.HTTPError as e:
        # Extract the error details from the response
        try:
            error_details = response.json().get("detail", "An unknown error occurred.")
        except Exception:
            error_details = "An unknown error occurred."
        await send_error_message(
            interaction,
            title="Error Settling Debts!",
            description=f"{error_details}"
         )
        return
    except requests.exceptions.RequestException as e:
        await send_error_message(
            interaction,
            title="You messed it up bro",
            description=f"Error: {e}"
         )
        return

    # Send confirmation message
    settled_amount = currency_formatter(data["settled_amount"])
    remaining_amount = currency_formatter(data["remaining_amount"])
    await send_success_message(
        interaction,
        title="Debt Settled Successfully",
        description=  f"Settled {settled_amount} with {user.mention}. Remaining debt: {remaining_amount}."
    )

@bot.tree.command(name="set_unicode_preference", description="Set your default preference for using Unicode fractions.")
@app_commands.describe(use_unicode="Set to True to use Unicode fractions, False otherwise.")
async def set_unicode_preference(interaction: discord.Interaction, use_unicode: bool):
    user_id = interaction.user.id  # Get the user's ID

    # Call the external API to update the preference
    try:
        payload = {"user_id": user_id, "use_unicode": use_unicode}
        response = requests.post(f"{API_URL}/set_preference", json=payload)
        response.raise_for_status()
        data = response.json()
    except requests.exceptions.RequestException as e:
        await send_error_message(
            interaction,
            title="Error Updating Preference",
            description=f"An error occurred while updating your preference: {e}"
        )
        return

    # Provide feedback to the user
    await send_success_message(
        interaction,
        title="Preference Updated",
        description=f"Your default preference for Unicode fractions has been set to: **{'Enabled' if use_unicode else 'Disabled'}**.\nHope you enjoy being able to see the {CURRENCY_NAME} economy in your preffered way!"
    )

bot.run(BOT_TOKEN)