import discord
from discord.ext import commands
from pydantic import ValidationError
from bot_commands import register_commands
from bot_config import load_config
from error_messages import ERROR_MESSAGES
import api_client
from send_messages import send_error_message
import requests

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

def format_error_message(error_message: str):
    """
    Formats the error message with values from config.
    """
    config = get_config()
    return error_message.format(
            CURRENCY=config["CURRENCY_NAME"],
            CURRENCY_PLURAL=config["CURRENCY_NAME_PLURAL"],
            MAX_DEBT=config["MAXIMUM_PER_DEBT"],
            SMALLEST_UNIT=config["SMALLEST_UNIT"],
            BOT_NAME=config["BOT_NAME"],
        )

def get_error_message(error_code: str):
    """
    Retrieves and formats an error message from ERROR_MESSAGES
    """
    error = ERROR_MESSAGES.get(error_code, ERROR_MESSAGES["UNKNOWN_ERROR"])
    return {
        "title": format_error_message(error["title"]),
        "description": format_error_message(error["description"])
    }

def parse_api_error(e: requests.exceptions.HTTPError):
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

def main():
    """
    Main function to run the bot.
    """
    bot.run(get_config()["BOT_TOKEN"])

if __name__ == "__main__":
    main()