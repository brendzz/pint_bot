"""Module for defining bot commands."""
import discord
from discord import app_commands
from bot.setup.command import Command
from bot.commands.debt_display import handle_debts_with_user, handle_get_all_debts, handle_get_debts, handle_get_transactions
from bot.commands.debt_management import handle_owe, handle_settle, handle_cashout
from bot.commands.games import handle_roll
from bot.commands.support import handle_help_command, handle_repeat_that_command
from bot.commands.bot_settings import handle_settings
from bot.commands.user_settings import handle_set_unicode_preference, handle_refresh_name
import bot.config as config

def define_command_details() -> None:
    """Define the command details for the bot."""
    Command._registry.clear()

    Command(
        key="help",
        name="help",
        description="Get a list of available commands and their descriptions.",
        category=config.SUPPORT_COMMAND_CATEGORY
    )

    Command(
        key="repeat_that",
        name="repeat_that",
        description="Resend the last bot message for this channel but in all capitals",
        category=config.SUPPORT_COMMAND_CATEGORY
    )

    Command(
        key="debts_with_user",
        name=config.DEBTS_WITH_USER_COMMAND,
        description=f"See current {config.CURRENCY_NAME} debts between yourself and another user.",
        category=config.DEBT_DISPLAY_COMMAND_CATEGORY
    )

    Command(
        key="get_debts",
        name=config.GET_DEBTS_COMMAND,
        description=f"See current {config.CURRENCY_NAME} debts for yourself or another user.",
        category=config.DEBT_DISPLAY_COMMAND_CATEGORY
    )

    Command(
        key="get_all_debts",
        name=config.GET_ALL_DEBTS_COMMAND,
        description=f"See everyone's total {config.CURRENCY_NAME} debts.",
        category=config.DEBT_DISPLAY_COMMAND_CATEGORY
    )

    Command(
        key="transactions",
        name="transactions",
        description="See debt transactions between specified dates",
        category=config.DEBT_DISPLAY_COMMAND_CATEGORY
    )

    Command(
        key="owe",
        name="owe",
        description=f"Add a number of {config.CURRENCY_NAME_PLURAL} you owe someone.",
        category=config.DEBT_TRANSACTIONS_COMMAND_CATEGORY
    )

    Command(
        key="settle",
        name="settle",
        description=(
            f"Settle {config.CURRENCY_NAME} debts you owe someone."
        ),
        category=config.DEBT_TRANSACTIONS_COMMAND_CATEGORY
    )

    Command(
        key="cashout",
        name="cashout",
        description=(
            f"Cashout your {config.CURRENCY_NAME} debts from someone."
        ),
        category=config.DEBT_TRANSACTIONS_COMMAND_CATEGORY
    )

    Command(
        key="set_unicode_preference",
        name="set_unicode_preference",
        description="Set your default preference for using Unicode fractions.",
        category=config.SETTINGS_COMMAND_CATEGORY
    )

    Command(
        key="settings",
        name="settings",
        description="View the current bot settings.",
        category=config.SETTINGS_COMMAND_CATEGORY
    )

    Command(
        key="refresh_name",
        name="refresh_name",
        description=(
            "Refresh the name the bot stores for you for if you update your discord username"
        ),
        category=config.SETTINGS_COMMAND_CATEGORY
    )

    Command(
        key="roll",
        name=config.ROLL_COMMAND,
        description=f"Play {config.ROLL_COMMAND} game.",
        category=config.GAMES_COMMAND_CATEGORY
    )

def register_commands(bot):
    """Registers the bot commands with the Discord API."""
    define_command_details()

    @bot.tree.command(
        name=Command.get("help").name,
        description=Command.get("help").description
    )
    async def help_command(interaction: discord.Interaction):
        await handle_help_command(interaction)

    @bot.tree.command(
        name=Command.get("repeat_that").name,
        description=Command.get("repeat_that").description
    )
    async def repeat_that_command(interaction: discord.Interaction):
        await handle_repeat_that_command(interaction)

    @bot.tree.command(
        name=Command.get("owe").name,
        description=Command.get("owe").description
    )
    @app_commands.describe(
        user="Who you owe",
        amount=f"How many {config.CURRENCY_NAME_PLURAL} to owe",
        reason="Why you owe them (optional)"
    )
    async def owe(interaction: discord.Interaction, user: discord.User, amount: str, *, reason: str = ""):
        await handle_owe(interaction, user, amount, reason=reason)

    @bot.tree.command(
        name=Command.get("get_debts").name,
        description=Command.get("get_debts").description
    )
    @app_commands.describe(
        user="Another user to view debts for",
        show_details=f"Show details of each individual debt (Default:{config.SHOW_DETAILS_DEFAULT})",
        show_percentages=f"Display percentages of how much of the economy each person owes/is owed (Default: {config.SHOW_PERCENTAGES_DEFAULT})",
        show_conversion_currency=(
            f"Show the equivalent value of the debts in {config.CONVERSION_CURRENCY} "
            f"(Default: {config.SHOW_CONVERSION_CURRENCY_DEFAULT})"
        ),
        show_emoji_visuals=(
                f"Visualise the worth of the debts with {config.CURRENCY_DISPLAY_EMOJI} emojis "
                f"(Default: {config.SHOW_EMOJI_VISUALS_DEFAULT})"
        )
    )
    async def get_debts(interaction: discord.Interaction, 
                        user: discord.User = None, 
                        show_details: bool = None, 
                        show_percentages: bool = None, 
                        show_conversion_currency: bool = None, 
                        show_emoji_visuals: bool = None):
        await handle_get_debts(interaction, user, show_details, show_percentages, show_conversion_currency, show_emoji_visuals)

    @bot.tree.command(
        name=Command.get("get_all_debts").name,
        description=Command.get("get_all_debts").description
    )
    @app_commands.describe(
        table_format=f"Display in table format (not recommended for mobile, Default: {config.USE_TABLE_FORMAT_DEFAULT}).",
        show_percentages=(
            "Display percentages of how much of the economy each person owes/is owed "
            f"(Default: {config.SHOW_PERCENTAGES_DEFAULT})"
        ),
        show_conversion_currency=(
                f"Show the worth of the debts in {config.CONVERSION_CURRENCY} "
                f"(Default: {config.SHOW_CONVERSION_CURRENCY_DEFAULT})"
            ),
        show_emoji_visuals=(
                f"Visualise the worth of the debts with {config.CURRENCY_DISPLAY_EMOJI} emojis "
                f"(Default: {config.SHOW_EMOJI_VISUALS_DEFAULT})"
            )
    )
    async def get_all_debts(interaction: discord.Interaction, table_format: bool = None, show_percentages: bool = None, show_conversion_currency: bool = None, show_emoji_visuals: bool = None):
        await handle_get_all_debts(interaction, table_format, show_percentages, show_conversion_currency, show_emoji_visuals)

    @bot.tree.command(
        name=Command.get("debts_with_user").name,
        description=Command.get("debts_with_user").description
    )
    @app_commands.describe(
        user="The user to view your debts with",
        show_details=(
            "Show details of each debt "
            f"(Default: {config.SHOW_DETAILS_DEFAULT})"
        ),
        show_percentages=(
            "Display percentages of how much each person owes/is owed "
            f"(Default: {config.SHOW_PERCENTAGES_DEFAULT})"
        ),
        show_conversion_currency=(
            f"Show the worth of the debts in {config.CONVERSION_CURRENCY} "
            f"(Default: {config.SHOW_CONVERSION_CURRENCY_DEFAULT})"
        ),
        show_emoji_visuals=(
                f"Visualise the worth of the debts with {config.CURRENCY_DISPLAY_EMOJI} emojis "
                f"(Default: {config.SHOW_EMOJI_VISUALS_DEFAULT})"
        )
    )
    async def debts_with_user(
        interaction: discord.Interaction,
        user: discord.User,
        show_details: bool = None,
        show_percentages: bool = None,
        show_conversion_currency: bool = None,
        show_emoji_visuals: bool = None
    ):
        await handle_debts_with_user(interaction, user, show_details, show_percentages, show_conversion_currency, show_emoji_visuals)

    @bot.tree.command(
        name=Command.get("transactions").name,
        description=Command.get("transactions").description
    )
    @app_commands.describe(
        start_date=(
            "Start Date "
            f"(Default: {config.TRANSACTIONS_DEFAULT_TIME_PERIOD} days in the past)"
        ),
        end_date=(
            "End Date  "
            "(Default: Today)"
        ),
        user_id="User to get transactions for (optional)",
        transaction_type="Type: owe or settle (optional)",
        show_conversion_currency=(
            f"Show the worth of the debts in {config.CONVERSION_CURRENCY} "
            f"(Default: {config.SHOW_CONVERSION_CURRENCY_DEFAULT})"
        ),
        show_emoji_visuals=(
                f"Visualise the worth of the debts with {config.CURRENCY_DISPLAY_EMOJI} emojis "
                f"(Default: {config.SHOW_EMOJI_VISUALS_DEFAULT})"
        ),
        display_as_settle=(
                f"Display as 'Settles' rather than 'Cashouts'"
                f"(Default: {config.DISPLAY_TRANSACTIONS_AS_SETTLE_DEFAULT})"
        )
    )
    async def transactions_command(
        interaction: discord.Interaction,
        start_date: str = None,
        end_date: str = None,
        user_id: str = None,
        transaction_type: str = None,
        show_conversion_currency: bool = None,
        show_emoji_visuals: bool = None,
        display_as_settle: bool = None
    ):
        await handle_get_transactions(interaction, start_date, end_date, user_id, transaction_type, show_conversion_currency, show_emoji_visuals, display_as_settle)

                                    
    @bot.tree.command(
        name=Command.get("settle").name,
        description=Command.get("settle").description
    )
    @app_commands.describe(
        user="Who you want to settle debts with",
        amount=f"How many {config.CURRENCY_NAME_PLURAL} to settle",
        reason="Reason to show with this transaction (optional)"
    )
    async def settle(interaction: discord.Interaction, user: discord.User, amount: str, reason: str = ""):
        await handle_settle(interaction, user, amount, reason=reason)

    @bot.tree.command(
            name=Command.get("cashout").name,
            description=Command.get("cashout").description
        )
    @app_commands.describe(
        user="Who you want to cashout debts from",
        amount=f"How many {config.CURRENCY_NAME_PLURAL} to cashout",
        reason="Reason to show with this transaction (optional)"
    )
    async def cashout(interaction: discord.Interaction, user: discord.User, amount: str, reason: str = ""):
        await handle_cashout(interaction, user, amount, reason=reason)

    @bot.tree.command(
        name=Command.get("set_unicode_preference").name,
        description=Command.get("set_unicode_preference").description
    )
    @app_commands.describe(
        use_unicode="Set to True to use Unicode fractions, False otherwise."
    )
    async def set_unicode_preference(interaction: discord.Interaction, use_unicode: bool):
        await handle_set_unicode_preference(interaction, use_unicode)

    @bot.tree.command(
        name=Command.get("settings").name,
        description=Command.get("settings").description
    )
    @app_commands.describe(
        table_format=f"Display in table format (not recommended for mobile, Default: {config.USE_TABLE_FORMAT_DEFAULT})."
    )
    async def settings(interaction: discord.Interaction, table_format: bool = None):
        await handle_settings(interaction, table_format)

    @bot.tree.command(
        name=Command.get("refresh_name").name,
        description=Command.get("refresh_name").description
    )
    async def refresh_name(interaction: discord.Interaction):
        await handle_refresh_name(interaction)

    @bot.tree.command(
        name=Command.get("roll").name,
        description=Command.get("roll").description
    )
    async def roll(interaction: discord.Interaction):
        await handle_roll(interaction)
