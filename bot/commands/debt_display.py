from fractions import Fraction
import discord
from bot import api_client, config
from bot.utilities.error_handling import handle_error
from bot.utilities.formatter import currency_formatter, to_percentage, with_conversion_currency, with_emoji_visuals
import bot.utilities.send_messages as send_messages
from bot.utilities.user_preferences import fetch_unicode_preference
from bot.utilities.user_utils import get_display_name

def with_percentage(value: Fraction, total: Fraction, string_amount:str) -> str:
    """Format a debt with its percentage of the total."""
    formatted = f"{string_amount} {to_percentage(value, total, config.PERCENTAGE_DECIMAL_PLACES)}"
    return formatted

def format_individual_debt_entries(
    entries,
    total: Fraction,
    use_unicode: bool,
    show_details: bool,
    show_percentages: bool,
    show_conversion_currency: bool,
    show_emoji_visuals: bool
) -> list[str]:
    """Format debt entries for display."""
    lines = []
    total_amount = sum(Fraction(entry['amount']) for entry in entries)
    total_formatted = currency_formatter(total_amount, use_unicode)
    if show_conversion_currency:
        total_formatted = with_conversion_currency(total_amount, total_formatted)
    if show_emoji_visuals:
        total_formatted = with_emoji_visuals(total_amount, total_formatted)
    lines.append(total_formatted)
    
    if show_details:
        for entry in entries:
            amount = currency_formatter(entry["amount"], use_unicode)
            if show_conversion_currency:
                amount = with_conversion_currency(entry["amount"], amount)
            if show_percentages:
                amount = with_percentage(entry["amount"], total, amount)
            if show_emoji_visuals:
                amount = with_emoji_visuals(entry["amount"], amount, False)
            if entry['reason']!="":
                lines.append(f"- {amount} for *{entry['reason']}* on {entry['timestamp']}")
            else:
                lines.append(f"- {amount} for *[No Reason Given]* on {entry['timestamp']}")
    return lines

def format_overall_debts(
        total_owed: Fraction,
        show_conversion_currency: bool,
        show_emoji_visuals: bool,
        use_unicode: bool):
    total_owed_formatted = currency_formatter(total_owed, use_unicode).upper()
    if show_conversion_currency:
        total_owed_formatted=with_conversion_currency(total_owed, total_owed)
    if show_emoji_visuals:
        total_owed_formatted=with_emoji_visuals(total_owed, total_owed_formatted)

    return(
        f"{total_owed_formatted}"
    )

def find_net_difference(owed_to_you: Fraction,
        owed_by_you: Fraction,
        use_unicode: bool,
        show_conversion_currency: bool,
        show_emoji_visuals: bool) -> str:
    net_difference = owed_to_you - owed_by_you
    net_difference_formatted = currency_formatter(abs(net_difference), use_unicode)
    if show_conversion_currency:
         net_difference_formatted = with_conversion_currency(net_difference, net_difference_formatted)
    if show_emoji_visuals:
         net_difference_formatted = with_emoji_visuals(net_difference, net_difference_formatted)
    
    if net_difference>0:
        return(f"\n__**NET DIFFERENCE - OWED TO YOU:**__ {net_difference_formatted}\nYou are in the positive!")
    elif net_difference<0:
        return(f"\n__**NET DIFFERENCE - YOU OWE:**__ {net_difference_formatted}\nYou are in the negative!")
    else:
        return(f"\nPerfectly balanced!")


async def handle_get_debts(interaction: discord.Interaction, 
                           user: discord.User = None, 
                           show_details: bool = None, 
                           show_percentages: bool = None,
                           show_conversion_currency: bool = None,
                           show_emoji_visuals: bool = None):
    """Handle fetching and displaying user debts for one user."""
    show_percentages = config.SHOW_PERCENTAGES_DEFAULT if show_percentages is None else show_percentages
    show_conversion_currency = config.SHOW_CONVERSION_CURRENCY_DEFAULT if show_conversion_currency is None else show_conversion_currency
    show_emoji_visuals = config.SHOW_EMOJI_VISUALS_DEFAULT if show_emoji_visuals is None else show_emoji_visuals
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
            lines.append(f"\n**{creditor_name}**: {entry_lines[0]}")
            lines.extend(entry_lines[1:])

    # Debts owed to the user
    if data["owed_to_you"]:
        total_owed_to_you = Fraction(data['total_owed_to_you'])
       
        lines.append(f"\n__**{config.CURRENCY_NAME_PLURAL} OWED TO {'YOU' if user is None else 'THEM'}:**__ {format_overall_debts(total_owed_to_you,show_conversion_currency,show_emoji_visuals,use_unicode)}")
        for debtor_id, entries in data["owed_to_you"].items():
            debtor_name = await get_display_name(interaction.client, debtor_id)
            entry_lines = format_individual_debt_entries(entries, total_owed_to_you, use_unicode, show_details, show_percentages, show_conversion_currency, show_emoji_visuals_on_details)
            lines.append(f"\n**{debtor_name}**: {entry_lines[0]}")
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
    table_format = config.USE_TABLE_FORMAT_DEFAULT if table_format is None else table_format
    show_percentages = config.SHOW_PERCENTAGES_DEFAULT if show_percentages is None else show_percentages
    show_conversion_currency = config.SHOW_CONVERSION_CURRENCY_DEFAULT if show_conversion_currency is None else show_conversion_currency
    show_emoji_visuals = config.SHOW_EMOJI_VISUALS_DEFAULT if show_emoji_visuals is None else show_emoji_visuals

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
    show_percentages = config.SHOW_PERCENTAGES_DEFAULT if show_percentages is None else show_percentages
    show_conversion_currency = config.SHOW_CONVERSION_CURRENCY_DEFAULT if show_conversion_currency is None else show_conversion_currency
    show_emoji_visuals = config.SHOW_EMOJI_VISUALS_DEFAULT if show_emoji_visuals is None else show_emoji_visuals

    user_id1 = str(interaction.user.id)
    user_id2 = str(user.id)

    # Defer the interaction to avoid timeout
    await interaction.response.defer()

    # Call the external API to fetch debts
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
