import discord
from bot import api_client
from bot import config
from bot.utilities.error_handling import handle_error
from bot.utilities.formatter import currency_formatter
import bot.utilities.send_messages as send_messages
from bot.utilities.user_preferences import fetch_unicode_preference
from bot.utilities.debt_processor import find_net_difference
from models.owe_request import OweRequest
from models.settle_request import SettleRequest
from fractions import Fraction

async def handle_owe(interaction: discord.Interaction, user: discord.User, amount: str, *, reason: str = ""):
    debtor = interaction.user.id
    creditor = user.id

    # Defer the response to avoid timeout
    await interaction.response.defer()

    if debtor == creditor:
        await handle_error(interaction, error_code="CANNOT_OWE_SELF")
        return
    elif creditor == interaction.client.user.id:
        await handle_error(interaction, error_code="CANNOT_OWE_BOT")
        return

    # Call the external API
    try:
        owe_request = OweRequest(
            debtor=debtor,
            creditor=creditor,
            amount=amount,
            reason=reason
        )
        payload = owe_request.model_dump()
        data = api_client.add_debt(payload)
    except Exception as e:
        await handle_error(interaction, e, title="Error Adding Debt")
        return

    use_unicode = await fetch_unicode_preference(interaction, interaction.user.id)

    debts_remaining = api_client.debts_with_user(debtor, creditor)
    total_owed_by_you = Fraction(debts_remaining['total_owed_by_you'])
    total_owed_to_you = Fraction(debts_remaining['total_owed_to_you'])
    formatted_reason = f" for: *'{data['reason']}'*" if data['reason'] else ""

    message = (f"**Added {currency_formatter(data['amount'], use_unicode)} owed to {user.mention}**{formatted_reason}"
            f"\n\nNew Total Debt to {user.mention} - You Owe {currency_formatter(total_owed_by_you, use_unicode)}")
    
    await send_messages.send_success_message(
            interaction,
            title=f"{currency_formatter(data["amount"], False)} Debt Added - {config.CURRENCY_NAME} Economy Thriving",
            description=message
        )

async def handle_settle(interaction: discord.Interaction, user: discord.User, amount: str, reason: str = ""):
    debtor = interaction.user.id
    creditor = user.id

    if debtor == creditor:
        await handle_error(interaction, error_code="CANNOT_SETTLE_SELF")
        return
    elif creditor == interaction.client.user.id:
        await handle_error(interaction, error_code="CANNOT_SETTLE_BOT")
        return

    # Defer the response to avoid timeout
    await interaction.response.defer()

    # Call the external API to settle debts
    try:
        # Use the SettleRequest Pydantic model to validate the payload
        settle_request = SettleRequest(
            debtor=debtor,
            creditor=creditor,
            amount=amount,
            reason=reason
        )
        payload = settle_request.model_dump()

        # Send the request to the API
        data = api_client.settle_debt(payload)

    except Exception as e:
        await handle_error(interaction, e, title="Error Settling Debt")
        return

    use_unicode = await fetch_unicode_preference(interaction, interaction.user.id)

    # Send confirmation message
    settled_amount = currency_formatter(data["settled_amount"], use_unicode)
    remaining_amount = currency_formatter(data["remaining_amount"], use_unicode)
    formatted_reason = f"\n*{reason}*" if reason else ""
    await send_messages.send_success_message(
        interaction,
        title="Debt Settled Successfully",
        description= f"Settled {settled_amount} with {user.mention}.{formatted_reason}\n\nRemaining debt: {remaining_amount}."
    )

async def handle_cashout(interaction: discord.Interaction, user: discord.User, amount: str, reason: str = ""):
    debtor = user.id
    creditor = interaction.user.id

    if debtor == creditor:
        await handle_error(interaction, error_code="CANNOT_SETTLE_SELF")
        return

    # Defer the response to avoid timeout
    await interaction.response.defer()

    # Call the external API to settle debts
    try:
        # Use the SettleRequest Pydantic model to validate the payload
        settle_request = SettleRequest(
            debtor=debtor,
            creditor=creditor,
            amount=amount,
            reason=reason
        )
        payload = settle_request.model_dump()

        # Send the request to the API
        data = api_client.settle_debt(payload)

    except Exception as e:
        await handle_error(interaction, e, title="Error Cashing Out Debt")
        return

    use_unicode = await fetch_unicode_preference(interaction, interaction.user.id)

    # Send confirmation message
    settled_amount = currency_formatter(data["settled_amount"], use_unicode)
    remaining_amount = currency_formatter(data["remaining_amount"], use_unicode)
    formatted_reason = f"\n*{reason}*" if reason else ""
    await send_messages.send_success_message(
        interaction,
        title=f"{currency_formatter(data["settled_amount"], False)} Debt Cashed Out Successfully",
        description= f"Cashed out {settled_amount} from {user.mention}.{formatted_reason}\n\nRemaining debt: {remaining_amount}."
    )
