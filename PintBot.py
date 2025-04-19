import discord
from discord.ext import commands
from discord import app_commands
from fractions import Fraction
from datetime import datetime
from os import environ
from dotenv import load_dotenv
from pint_formatter import pint_formatter
from OweRequest import OweRequest
from pydantic import ValidationError, field_validator
import requests



intents = discord.Intents.default()
intents.message_content = True

load_dotenv()

CONST_BOT_TOKEN = environ["CONST_BOT_TOKEN"]
CONST_API_URL = environ["CONST_API_URL"]

bot = commands.Bot("!",intents=intents)

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user} (ID: {bot.user.id})")
    print("------")
    await bot.tree.sync()

#Add a pint debt
@bot.tree.command(name="owe", description="Add a number of pints you owe someone.")
@app_commands.describe(user="Who you owe", pint_number="How many pints", reason="Why you owe them (optional)")
async def owe(interaction: discord.Interaction, user: discord.User, pint_number: str, *, reason: str = ""):
    debtor = interaction.user.id
    creditor = user.id

    if debtor == creditor:
        await interaction.response.send_message("You can't owe yourself pints, that would be too confusing sorry.")
        return
    elif creditor == bot.user.id:
        await interaction.response.send_message("#Pint Bot already has plenty of pints, but thanks for the generous offer!")
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
        print(payload)
        response = requests.post(
            f"{CONST_API_URL}/owe",
            json=payload
        )
        print(response)
        response.raise_for_status()
        data = response.json()
        print(data)

    except requests.exceptions.HTTPError as e:
        # Extract the error details from the response
        try:
            error_details = response.json().get("detail", "An unknown error occurred.")
            if isinstance(error_details, list):
                error_message = "; ".join([err["msg"] for err in error_details])
            else:
                error_message = error_details
        except Exception:
            error_message = "An unknown error occurred."
        
        await interaction.followup.send(f"{error_message}")
        return
    
    except requests.exceptions.RequestException as e:
        await interaction.followup.send(f"Error: {e}")
        return

    except ValidationError as e:
        await interaction.followup.send(f"Looks like you've got some invalid data there buddy - we've 200 character limits around these parts.")
        return

    except Exception as e:
        await interaction.followup.send(f"You really broke it man :(. Error: {e}")
        return
    await interaction.followup.send(
        f"Added {pint_formatter(data['amount'])} owed to {user.mention} for: *{data['reason']}* at {data['timestamp']}"
    )

#See your own pint debts
@bot.tree.command(name="pints", description="See your current pint debts.")
async def pints(interaction: discord.Interaction):
    user_id = interaction.user.id

    # Call the external API to fetch debts
    try:
        response = requests.get(f"{CONST_API_URL}/pints/{user_id}")
        response.raise_for_status()
        data = response.json()
    except requests.exceptions.RequestException as e:
        await interaction.response.send_message(f"Error fetching pint debts: {e}")
        return

    # Check if the API returned a "message" field (no debts found)
    if "message" in data:
        await interaction.response.send_message(data["message"])
        return

    # Format the response
    lines = []

    # Debts owed by the user
    if data["owed_by_you"]:
        lines.append(f"__**PINTS YOU OWE:**__ {pint_formatter(data["total_owed_by_you"]).upper()}")
        for creditor_id, entries in data["owed_by_you"].items():
            try:
                creditor = await bot.fetch_user(int(creditor_id))  # Fetch the creditor's username
                creditor_name = creditor.display_name
            except discord.NotFound:
                creditor_name = f"Unknown User ({creditor_id})"
            lines.append(f"\n**{creditor_name}**: {pint_formatter(sum(Fraction(entry["amount"]) for entry in entries))}")
            for entry in entries:
                amount = entry["amount"]
                reason = entry["reason"]
                timestamp = entry["timestamp"]
                lines.append(f"- {amount} pints for *{reason}* on {timestamp}")

    # Debts owed to the user
    if data["owed_to_you"]:
        lines.append(f"\n__**PINTS OWED TO YOU:**__ {pint_formatter(data["total_owed_to_you"]).upper()}")
        for debtor_id, entries in data["owed_to_you"].items():
            try:
                debtor = await bot.fetch_user(int(debtor_id))  # Fetch the debtor's username
                debtor_name = debtor.display_name
            except discord.NotFound:
                debtor_name = f"Unknown User ({debtor_id})"
            
            lines.append(f"\n**{debtor_name}**: {pint_formatter(sum(Fraction(entry["amount"]) for entry in entries))}")
            for entry in entries:
                amount = entry["amount"]
                reason = entry["reason"]
                timestamp = entry["timestamp"]
                lines.append(f"- {amount} pints for *{reason}* on {timestamp}")

    # Send the formatted response
    await interaction.response.send_message("\n".join(lines))


#See everyone's pints
"""
@bot.tree.command(name="allpints", description="See everyone's current pint debts.")
async def allpints(interaction: discord.Interaction):
    summary = {}
    for debtor, creditors in debts.items():
        for creditor, entries in creditors.items():
            summary[(debtor, creditor)] = summary.get((debtor, creditor), Fraction(0)) + sum(entry[0] for entry in entries)

    if not summary:
        await interaction.response.send_message("No one owes anyone pints. The pint economy is in shambles.")
        return

    lines = []
    for (debtor_id, creditor_id), total in summary.items():
        debtor = await bot.fetch_user(debtor_id)
        creditor = await bot.fetch_user(creditor_id)
        lines.append(f"{debtor.display_name} owes {creditor.display_name}: {pint_formatter(total)}")

    await interaction.response.send_message("\n".join(lines))
"""
    
# Replace with your bot token
bot.run(CONST_BOT_TOKEN)