import discord
from bot import config
from bot.command import Command
import bot.utilities.send_messages as send_messages

async def handle_help_command(interaction: discord.Interaction):
    # Defer the interaction to avoid timeout
    await interaction.response.defer()

    # Format the response
    help_message = (
        f"My name is {config.BOT_NAME} and "
        f"I am here to help keep track of {config.CURRENCY_NAME} debts owed between users.\n\n"
        f"__**Commands:**__"
    )

    categorised_commands = Command.all_by_category()

    for category, commands in categorised_commands.items():

        # Add a header for each category
        help_message += f"\n**{category}:**\n"
        for command in commands:
            # Add the command name and description to the help message
            help_message += f"**/{command.name}** — {command.description}\n"

    help_message += f"\n__**What can you redeem each {config.CURRENCY_NAME} for?**__\n"
    for item in config.TRANSFERABLE_ITEMS:
        help_message += f"- {item}\n"

    # Send the help message
    await send_messages.send_info_message(
        interaction,
        title=f"{config.BOT_NAME} Help",
        description=help_message
    )
