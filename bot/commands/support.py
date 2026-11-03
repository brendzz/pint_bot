"""Support commands (help, etc.). Platform-agnostic."""
from bot import config
from bot.platform.context import CommandContext
from bot.setup.command import Command

async def handle_help_command(ctx: CommandContext):
    # Defer the interaction to avoid timeout
    await ctx.defer()

    # Format the response
    help_message = (
        f"My name is {config.BOT_NAME} and "
        f"I am here to help keep track of {config.CURRENCY_NAME} debts owed between users.\n\n"
        f"__**Commands:**__"
    )

    categorised_commands = Command.all_by_category()

    for category, commands in categorised_commands.items():

        # Add a header for each category
        help_message += f"\n__**{category}:**__\n"
        for command in commands:
            # Add the command name and description to the help message
            help_message += f"**/{command.name}** — {command.description}\n"

    help_message += f"\n\n__**What can you redeem each {config.CURRENCY_NAME} for?**__\n"
    for item in config.TRANSFERABLE_ITEMS:
        help_message += f"- {item}\n"

    # Send the help message
    await ctx.messenger.info(
        ctx,
        title=f"{config.BOT_NAME} Help",
        description=help_message
    )

async def handle_repeat_that_command(ctx: CommandContext):
    await ctx.defer()

    await ctx.messenger.info(
        ctx,
        title="REPEAT THAT",
        description="This command does not do anything yet sorry!"
    )
