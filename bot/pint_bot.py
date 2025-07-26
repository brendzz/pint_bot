"""Module for defining the main bot functionality."""
from os import environ
import random
import time
import discord
from discord.ext import commands
from dotenv import load_dotenv
import bot.config as config
from bot.setup.register_commands import register_commands
from bot.setup.update_settings_from_api import update_settings_from_api

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot("!", intents=intents)

@bot.event
async def on_ready():
    """Called when the bot is ready and connected to Discord."""
    print(f"Logged in as {bot.user} (ID: {bot.user.id})")
    print("--------------------------------------------------------------")
    start_time = time.perf_counter()
    register_commands(bot)
    await bot.tree.sync()
    await update_settings_from_api()
    end_time = time.perf_counter()
    elapsed = end_time - start_time
    print(f"Commands registered and API settings synced in {elapsed:.2f} seconds.")
    print("--------------------------------------------------------------")

@bot.event
async def on_message(message: discord.Message):
    """Called when a message is sent in a channel the bot can see."""
    # Ignore messages sent by the bot itself
    if message.author == bot.user:
        # last_bot_message[message.channel.id] = message.content
        return

    # React to messages containing the currency name if the feature is enabled
    if config.REACT_TO_MESSAGES_MENTIONING_CURRENCY:
        if config.CURRENCY_NAME.lower() in message.content.lower():
            try:
                if random.random() <= config.REACTION_ODDS:
                    if random.random() <= config.REACTION_ODDS_RARE:
                        await message.add_reaction(config.REACTION_EMOJI_RARE)
                    else:
                        await message.add_reaction(config.REACTION_EMOJI)
            except discord.Forbidden:
                print("Bot does not have permission to add reactions.")
            except discord.HTTPException as e:
                print(f"Failed to add reaction: {e}")

    # Check if the bot is explicitly mentioned (not just replied to)
    if bot.user in message.mentions and not message.reference:
        embed = discord.Embed(
            title=f"Hello {message.author.display_name}!",
            description=f"I am {config.BOT_NAME}!\nI am currently set to manage the {config.CURRENCY_NAME} economy.\nUse '/help' to learn more.",
            color=discord.Color.yellow()
        )
        embed.set_footer(text=f"{config.BOT_NAME} - Your Local Friendly {config.CURRENCY_NAME} Economy Assistant.")
        embed.set_thumbnail(url=bot.user.avatar.url)
        await message.channel.send(embed=embed)

    # Process other commands (important to include this to avoid breaking command handling)
    await bot.process_commands(message)

def main():
    """Main function to run the bot."""
    load_dotenv("bot/.env")
    token = environ.get("BOT_TOKEN")
    if not token:
        raise RuntimeError("BOT_TOKEN is missing or not loaded from .env")
    bot.run(token)

if __name__ == "__main__":
    main()
