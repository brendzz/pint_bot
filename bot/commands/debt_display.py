from fractions import Fraction
import discord
from bot import api_client, config
from bot.utilities.error_handling import handle_error
from bot.utilities.formatter import currency_formatter, to_percentage
import bot.utilities.send_messages as send_messages
from bot.utilities.user_preferences import fetch_unicode_preference
from models.debts_with_user_request import DebtsWithUser

#See either your own debts or those of another user
async def handle_get_debts(interaction: discord.Interaction, user: discord.User = None, show_details: bool = None, show_percentages: bool = None):
    if show_details is None:
        show_details = config.SHOW_DETAILS_DEFAULT

    if show_percentages is None:
        show_percentages = config.SHOW_PERCENTAGES_DEFAULT

    if user is None:
        user_id = str(interaction.user.id)
    else:
        user_id = str(user.id)

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
            description=f"No debts found owed to or from this user. That's kind of cringe, {" " if user is None else "tell them to"} get some {config.CURRENCY_NAME} debt bro."
        )
        return

    use_unicode = await fetch_unicode_preference(interaction, user_id)

    # Format the response
    lines = []

    # Debts owed by the user
    if data["owed_by_you"]:
        total_owed_by_you = Fraction(data['total_owed_by_you'])
        lines.append(f"__**{config.CURRENCY_NAME_PLURAL} {"YOU" if user is None else "THEY"} OWE:**__ {currency_formatter(total_owed_by_you, use_unicode).upper()}")
        for creditor_id, entries in data["owed_by_you"].items():
            try:
                creditor = await bot.fetch_user(int(creditor_id))  # Fetch the creditor's username
                creditor_name = creditor.display_name
            except discord.NotFound:
                creditor_name = f"Unknown User ({creditor_id})"
            lines.append(f"\n**{creditor_name}**: {currency_formatter(sum(Fraction(entry['amount']) for entry in entries), use_unicode)}")
            if show_details:
                for entry in entries:
                    amount = currency_formatter(entry["amount"], use_unicode)
                    if show_percentages:
                        amount+=f" {to_percentage(entry['amount'],total_owed_by_you, config.PERCENTAGE_DECIMAL_PLACES)}"
                    reason = entry["reason"]
                    timestamp = entry["timestamp"]
                    lines.append(f"- {amount} for *{reason}* on {timestamp}")

    # Debts owed to the user
    if data["owed_to_you"]:
        total_owed_to_you = Fraction(data['total_owed_to_you'])
        lines.append(f"\n__**{config.CURRENCY_NAME_PLURAL} OWED TO {"YOU" if user is None else "THEM"}:**__ {currency_formatter(total_owed_to_you, use_unicode).upper()}")
        for debtor_id, entries in data["owed_to_you"].items():
            try:
                debtor = await bot.fetch_user(int(debtor_id))  # Fetch the debtor's username
                debtor_name = debtor.display_name
            except discord.NotFound:
                debtor_name = f"Unknown User ({debtor_id})"

            lines.append(f"\n**{debtor_name}**: {currency_formatter(sum(Fraction(entry['amount']) for entry in entries), use_unicode)}")
            if show_details:
                for entry in entries:
                    amount = currency_formatter(entry["amount"], use_unicode)
                    if show_percentages:
                        amount+=f" {to_percentage(entry['amount'],total_owed_to_you, config.PERCENTAGE_DECIMAL_PLACES)}"
                    reason = entry["reason"]
                    timestamp = entry["timestamp"]
                    lines.append(f"- {amount} for *{reason}* on {timestamp}")

    # If no debts are found, return a message
    # Send the formatted response
    title_beginning = "Your" if user is None else f"Here are {user.display_name}'s"
    await send_messages.send_info_message(
        interaction,
        title=
            f"{title_beginning} {config.CURRENCY_NAME} debts *{interaction.user.display_name}*, "
            f"{'thanks' if user is None else 'thank them'} for participating in the {config.CURRENCY_NAME} economy!",
        description="\n".join(lines)
    )
    # Send the formatted response

#See a summary of everyone's debts
async def handle_get_all_debts(interaction: discord.Interaction, table_format: bool = None, show_percentages: bool = None, show_details: bool = None):
    if table_format is None:
        table_format = config.USE_TABLE_FORMAT_DEFAULT
    if show_percentages is None:
        show_percentages = config.SHOW_PERCENTAGES_DEFAULT

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
        try:
            user = await bot.fetch_user(int(user_id))  # Fetch the user's username
            user_name = user.display_name
        except discord.NotFound:
            user_name = f"Unknown User ({user_id})"

        owes = currency_formatter(totals['owes'], use_unicode)
        is_owed = currency_formatter(totals['is_owed'], use_unicode)

        if show_percentages:
            owes += f" {to_percentage(totals['owes'],total_in_circulation, config.PERCENTAGE_DECIMAL_PLACES)}"
            is_owed += f" {to_percentage(totals['is_owed'],total_in_circulation, config.PERCENTAGE_DECIMAL_PLACES)}"

        table_data.append({
            "name": user_name,
            "Owes": owes,
            "Is Owed": is_owed
        })

    # Determine the economy health message
    economy_health_message = (
        max(
            (
                health
                for health in config.ECONOMY_HEALTH_MESSAGES
                if total_in_circulation >= health["threshold"]
            ),
            key=lambda h: h["threshold"],
            default={"message": "The economy is in an unknown state"}
        )["message"]
    )

    # Call send_table_message to send the data as a table
    await send_messages.send_two_column_table_message(
        interaction,
        title=f"{config.CURRENCY_NAME} Economy Overview",
        description=f"{economy_health_message}\n\n**Total {config.CURRENCY_NAME_PLURAL} in circulation: {currency_formatter(total_in_circulation, use_unicode)}**",
        data=table_data,
        table_format=table_format
    )

#See your debts with one other user
async def handle_debts_with_user(
    interaction: discord.Interaction,
    user: discord.User,
    show_details: bool = None,
    show_percentages: bool = None
):
    if show_details is None:
        show_details = config.SHOW_DETAILS_DEFAULT

    if show_percentages is None:
        show_percentages = config.SHOW_PERCENTAGES_DEFAULT

    user_id = str(user.id)

    # Defer the interaction to avoid timeout
    await interaction.response.defer()

    # Call the external API to fetch debts
    try:
        debts_with_user_request = DebtsWithUser(
            user_id=str(interaction.user.id),
            other_user_id=user_id
        )
        payload = debts_with_user_request.model_dump()
        data = api_client.debts_with_user(payload)
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

    use_unicode = await fetch_unicode_preference(interaction, user_id)

    # Format the response
    lines = []

    # Debts owed by the user
    if data["owed_by_you"]:
        total_owed_by_you = Fraction(data['total_owed_by_you'])
        lines.append(
            f"__**{config.CURRENCY_NAME_PLURAL} YOU OWE THEM:**__ "
            f"{currency_formatter(total_owed_by_you, use_unicode).upper()}"
        )
        for debt in data["owed_by_you"]:
            if show_details:
                amount = currency_formatter(debt["amount"], use_unicode)
                if show_percentages:
                    amount += f" {to_percentage(debt['amount'], total_owed_by_you, config.PERCENTAGE_DECIMAL_PLACES)}"
                reason = debt["reason"]
                timestamp = debt["timestamp"]
                lines.append(f"- {amount} for *{reason}* on {timestamp}")

    # Debts owed to the user
    if data["owed_to_you"]:
        total_owed_to_you = Fraction(data['total_owed_to_you'])
        lines.append(
            f"__**{config.CURRENCY_NAME_PLURAL} THEY OWE YOU:**__ "
            f"{currency_formatter(total_owed_to_you, use_unicode).upper()}"
        )
        for debt in data["owed_to_you"]:
            if show_details:
                amount = currency_formatter(debt["amount"], use_unicode)
                if show_percentages:
                    amount += f" {to_percentage(debt['amount'], total_owed_to_you, config.PERCENTAGE_DECIMAL_PLACES)}"
                reason = debt["reason"]
                timestamp = debt["timestamp"]
                lines.append(f"- {amount} for *{reason}* on {timestamp}")

    # If no debts are found, return a message
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
    # Send the formatted response
