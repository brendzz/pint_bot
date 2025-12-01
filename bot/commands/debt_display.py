from fractions import Fraction
import discord
from bot import api_client, config
from bot.utilities.error_handling import handle_error
from bot.utilities.formatter import currency_formatter, with_percentage, with_conversion_currency, with_emoji_visuals, format_overall_debts, format_individual_debt_entries, format_date, sanitize_dates
from bot.utilities.debt_processor import find_net_difference
from bot.utilities.transactions_processor import process_transaction
import bot.utilities.send_messages as send_messages
from bot.utilities.user_preferences import fetch_unicode_preference
from bot.utilities.user_utils import get_display_name
from bot.utilities.misc_utils import default_unless_included
from collections import defaultdict
from dateutil import parser
from dateutil.parser import isoparse

async def handle_get_debts(interaction: discord.Interaction, 
                           user: discord.User = None, 
                           show_details: bool = None, 
                           show_percentages: bool = None,
                           show_conversion_currency: bool = None,
                           show_emoji_visuals: bool = None):
    """Handle fetching and displaying user debts for one user."""
    show_percentages = default_unless_included(show_percentages, config.SHOW_PERCENTAGES_DEFAULT)
    show_conversion_currency = default_unless_included(show_conversion_currency, config.SHOW_CONVERSION_CURRENCY_DEFAULT)
    show_emoji_visuals = default_unless_included(show_emoji_visuals, config.SHOW_EMOJI_VISUALS_DEFAULT)
    user_id = str(interaction.user.id) if user is None else str(user.id)
    
    # Defer the interaction to avoid timeout
    await interaction.response.defer()
    # Call the external API to fetch debts
    try:
        data = api_client.get_debts(user_id)
    except Exception as e:
        await handle_error(interaction, e, title=f"Error Fetching {config.CURRENCY_NAME} Debts")
        return

    # Check if the API returned a "message" field (no debts found)
    if "message" in data:
        await send_messages.send_info_message(
            interaction,
            title=f"Looks like {"you're" if user is None else "they're"} not currently contributing to the {config.CURRENCY_NAME} economy.",
            description=f"No debts found owed to or from this user. That's kind of cringe, {"" if user is None else "tell them to"} get some {config.CURRENCY_NAME} debt bro."
        )
        return

    use_unicode = await fetch_unicode_preference(interaction, user_id)

    if show_emoji_visuals:
        show_emoji_visuals_on_details=config.SHOW_EMOJI_VISUALS_ON_DETAILS_DEFAULT
    else:
        show_emoji_visuals_on_details=False

    # Format the response
    lines = []

    # Debts owed by the user
    if data["owed_by_you"]:
        total_owed_by_you = Fraction(data['total_owed_by_you'])
                
        lines.append(f"__**{config.CURRENCY_NAME_PLURAL} {'YOU' if user is None else 'THEY'} OWE:**__ {format_overall_debts(total_owed_by_you,show_conversion_currency,show_emoji_visuals,use_unicode)}")
        for creditor_id, entries in data["owed_by_you"].items():
            creditor_name = await get_display_name(interaction.client, creditor_id)
            entry_lines = format_individual_debt_entries(entries, total_owed_by_you, use_unicode, show_details, show_percentages, show_conversion_currency, show_emoji_visuals_on_details)
            lines.append(f"\n**{creditor_name}:** {entry_lines[0]}")
            lines.extend(entry_lines[1:])

    # Debts owed to the user
    if data["owed_to_you"]:
        total_owed_to_you = Fraction(data['total_owed_to_you'])
       
        lines.append(f"\n__**{config.CURRENCY_NAME_PLURAL} OWED TO {'YOU' if user is None else 'THEM'}:**__ {format_overall_debts(total_owed_to_you,show_conversion_currency,show_emoji_visuals,use_unicode)}")
        for debtor_id, entries in data["owed_to_you"].items():
            debtor_name = await get_display_name(interaction.client, debtor_id)
            entry_lines = format_individual_debt_entries(entries, total_owed_to_you, use_unicode, show_details, show_percentages, show_conversion_currency, show_emoji_visuals_on_details)
            lines.append(f"\n**{debtor_name}:** {entry_lines[0]}")
            lines.extend(entry_lines[1:])

    # Send the formatted response
    title_beginning = "Your" if user is None else f"Here are {user.display_name}'s"
    await send_messages.send_info_message(
        interaction,
        title=
            f"{title_beginning} {config.CURRENCY_NAME} debts *{interaction.user.display_name}*, "
            f"{'thanks' if user is None else 'thank them'} for participating in the {config.CURRENCY_NAME} economy!",
        description="\n".join(lines)
    )

async def handle_get_all_debts(
    interaction: discord.Interaction,
    table_format: bool = None,
    show_percentages: bool = None,
    show_conversion_currency: bool = None,
    show_emoji_visuals: bool = None
):
    """Handle fetching and displaying user debts for all users."""
    table_format = default_unless_included(table_format, config.USE_TABLE_FORMAT_DEFAULT)
    show_percentages = default_unless_included(show_percentages, config.SHOW_PERCENTAGES_DEFAULT)
    show_conversion_currency = default_unless_included(show_conversion_currency, config.SHOW_CONVERSION_CURRENCY_DEFAULT)
    show_emoji_visuals = default_unless_included(show_emoji_visuals, config.SHOW_EMOJI_VISUALS_DEFAULT)

    # Emoji visuals and table format are mutually exclusive
    if table_format:
        show_emoji_visuals = False
    
    # Defer the interaction to avoid timeout
    await interaction.response.defer()

    # Call the external API to fetch all debts
    try:
        data = api_client.get_all_debts()
    except Exception as e:
        await handle_error(interaction, e, title=f"Error Fetching {config.CURRENCY_NAME} Debts")
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
        user_name = await get_display_name(interaction.client, user_id)
        owes = currency_formatter(totals['owes'], use_unicode)
        is_owed = currency_formatter(totals['is_owed'], use_unicode)

        if show_conversion_currency:
            owes = with_conversion_currency(totals['owes'], owes)
            is_owed = with_conversion_currency(totals['is_owed'], is_owed)

        if show_percentages:
            owes = with_percentage(totals['owes'], total_in_circulation, owes)
            is_owed = with_percentage(totals['is_owed'], total_in_circulation, is_owed)

        if show_emoji_visuals:
            owes = with_emoji_visuals(totals['owes'], owes)
            is_owed = with_emoji_visuals(totals['is_owed'], is_owed)

        table_data.append({
            "name": user_name,
            "Owes": owes,
            "Is Owed": is_owed
        })

    # Determine the economy health message
    economy_health_message = max(
        (
            health
            for health in config.ECONOMY_HEALTH_MESSAGES
            if total_in_circulation >= health["threshold"]
        ),
        key=lambda h: h["threshold"],
        default={"message": "The economy is in an unknown state"}
    )["message"]

    # Call send_table_message to send the data as a table
    await send_messages.send_two_column_table_message(
        interaction,
        title=f"{config.CURRENCY_NAME} Economy Overview",
        description=f"{economy_health_message}\n\n__**Total {config.CURRENCY_NAME_PLURAL} in circulation: {format_overall_debts(total_in_circulation,show_conversion_currency,show_emoji_visuals,use_unicode)}**__",
        data=table_data,
        table_format=table_format
    )

async def handle_debts_with_user(
    interaction: discord.Interaction,
    user: discord.User,
    show_details: bool = None,
    show_percentages: bool = None,
    show_conversion_currency: bool = None,
    show_emoji_visuals: bool = None
):
    """Handle fetching and displaying user debts between two users."""
    await interaction.response.defer()
    
    show_percentages = default_unless_included(show_percentages, config.SHOW_PERCENTAGES_DEFAULT)
    show_conversion_currency = default_unless_included(show_conversion_currency, config.SHOW_CONVERSION_CURRENCY_DEFAULT)
    show_emoji_visuals = default_unless_included(show_emoji_visuals, config.SHOW_EMOJI_VISUALS_DEFAULT)

    user_id1 = str(interaction.user.id)
    user_id2 = str(user.id)

    try:
        data = api_client.debts_with_user(user_id1, user_id2)
    except Exception as e:
        await handle_error(interaction, e, title=f"Error Fetching {config.CURRENCY_NAME} Debts")
        return

    # Check if the API returned a "message" field (no debts found)
    if "message" in data:
        await send_messages.send_info_message(
            interaction,
            title=f"Looks like there are no {config.CURRENCY_NAME} debts between you two.",
            description=(
                f"No {config.CURRENCY_NAME} debts found owed to or from this user. "
                f"That's kind of cringe, get more involved bro."
            )
        )
        return

    use_unicode = await fetch_unicode_preference(interaction, user_id1)

    # Format the response
    lines = []
    if show_emoji_visuals:
        show_emoji_visuals_on_details=config.SHOW_EMOJI_VISUALS_ON_DETAILS_DEFAULT
    else:
        show_emoji_visuals_on_details=False

    # Debts owed by the user
    total_owed_by_you = Fraction(data['total_owed_by_you'])
    if data["owed_by_you"]:

        lines.append(
            f"__**{config.CURRENCY_NAME_PLURAL} YOU OWE THEM:**__ "
            f"{format_overall_debts(total_owed_by_you,show_conversion_currency,show_emoji_visuals,use_unicode)}"
        )
        if show_details:
            lines.extend(format_individual_debt_entries(data["owed_by_you"], total_owed_by_you, use_unicode, show_details, show_percentages, show_conversion_currency, show_emoji_visuals_on_details))

    total_owed_to_you = Fraction(data['total_owed_to_you'])
    # Debts owed to the user
    if data["owed_to_you"]:
        lines.append(
            f"__**{config.CURRENCY_NAME_PLURAL} THEY OWE YOU:**__ "
            f"{format_overall_debts(total_owed_to_you,show_conversion_currency,show_emoji_visuals,use_unicode)}"
        )
        if show_details:
            lines.extend(format_individual_debt_entries(data["owed_to_you"], total_owed_to_you, use_unicode, show_details, show_percentages, show_conversion_currency, show_emoji_visuals_on_details))

    # Net difference
    lines.append(find_net_difference(total_owed_to_you,
                                     total_owed_by_you,
                                     use_unicode,
                                     show_conversion_currency,
                                     show_emoji_visuals))

    # Send the formatted response
    await send_messages.send_info_message(
        interaction,
        title=(
        f"Here are the {config.CURRENCY_NAME} debts between "
        f"*{interaction.user.display_name}* and *{user.display_name}*, "
        f"thank you for participating in the {config.CURRENCY_NAME} economy!"
    ),
        description="\n".join(lines)
    )

async def handle_get_transactions(
    interaction: discord.Interaction,
    start_date: str = None,
    end_date: str = None,
    user: discord.User = None,
    transaction_type: str = None,
    show_conversion_currency: bool = None,
    show_emoji_visuals: bool = None,
    display_as_settle: bool = True
):
    """Fetch and display transactions from the API."""
    await interaction.response.defer()

    show_conversion_currency = default_unless_included(show_conversion_currency, config.SHOW_CONVERSION_CURRENCY_DEFAULT)
    show_emoji_visuals = default_unless_included(show_emoji_visuals, config.SHOW_EMOJI_VISUALS_DEFAULT)
    display_as_settle = default_unless_included(display_as_settle, config.DISPLAY_TRANSACTIONS_AS_SETTLE_DEFAULT)
    
    start_date, end_date = sanitize_dates(start_date, end_date)
    user_id = None if user is None else str(user.id)

    if transaction_type and transaction_type.strip().lower() == "cashout":
        display_as_settle = False

    try:
        data = api_client.get_transactions(
            start_date=start_date,
            end_date=end_date,
            user_id=user_id,
            transaction_type=transaction_type
        )
    except Exception as e:
        await handle_error(interaction, e, title=f"Error Fetching {config.CURRENCY_NAME} Transactions")
        return

    if not data:
        await send_messages.send_info_message(
            interaction,
            title="No Transactions Found",
            description="No transactions found for the specified criteria."
        )
        return
        
    use_unicode = await fetch_unicode_preference(interaction, str(interaction.user.id))
    start_date = format_date(data["start_date"])
    end_date = format_date(data["end_date"])
    total_owed = Fraction(0)
    total_settled = Fraction(0)
    grouped = defaultdict(list)
    transactions = data["transactions"]
    for tx in transactions:
        date_str, tx_type, amount, line = await process_transaction(
        tx, config, interaction,
        show_conversion_currency, show_emoji_visuals,
        use_unicode, display_as_settle
    )

        if tx_type == "Owe":
            total_owed += amount
        elif tx_type == "Settle":
            total_settled += amount

        grouped[date_str].append(line)

    lines = []

    for date, txs in sorted(grouped.items()):
        lines.append(f"**{format_date(date)}**")
        lines.extend(txs)
        lines.append("")

    owed_str = format_overall_debts(total_owed, show_conversion_currency, show_emoji_visuals, use_unicode)
    settled_str = format_overall_debts(total_settled, show_conversion_currency, show_emoji_visuals, use_unicode)

    lines.append(f"**Total Owed In Period: {owed_str}**")
    lines.append(f"**Total {'Settled' if display_as_settle else 'Cashed Out'} In Period: {settled_str}**")
    lines.append(find_net_difference(total_owed,
                                     total_settled,
                                     use_unicode,
                                     show_conversion_currency,
                                     show_emoji_visuals,
                                     False))
    await send_messages.send_info_message(
        interaction,
        title=f"{config.CURRENCY_NAME} Transactions from {start_date} until {end_date}",
        description="\n".join(lines)
    )