"""Handlers for debt transactions (owe / settle / cashout).

These handlers are platform-agnostic: they speak
``bot.platform.CommandContext`` and ``PlatformUser`` only.
"""
import logging
from fractions import Fraction

from models.owe_request import OweRequest
from models.settle_request import SettleRequest

from bot import api_client
from bot import config
from bot.platform.context import CommandContext, PlatformUser
from bot.utilities.error_handling import handle_error
from bot.utilities.formatter import currency_formatter
from bot.utilities.user_preferences import fetch_unicode_preference

logger = logging.getLogger(__name__)

async def handle_owe(ctx: CommandContext, user: PlatformUser, amount: str, *, reason: str = ""):
    debtor = int(ctx.user_id)
    creditor = int(user.id)

    # Defer the response to avoid timeout
    await ctx.defer()

    if debtor == creditor:
        await handle_error(ctx, error_code="CANNOT_OWE_SELF")
        return
    elif str(creditor) == ctx.bot_user_id:
        await handle_error(ctx, error_code="CANNOT_OWE_BOT")
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
        data = await api_client.add_debt(payload)
    except Exception as e:
        await handle_error(ctx, e, title="Error Adding Debt")
        return

    use_unicode = await fetch_unicode_preference(ctx, ctx.user_id)

    formatted_reason = f" for: *'{data['reason']}'*" if data['reason'] else ""

    # Best effort: fetch the updated running total; the debt was added either way
    try:
        debts_remaining = await api_client.debts_with_user(str(debtor), str(creditor))
        total_owed_by_you = Fraction(debts_remaining['total_owed_by_you'])
        total_line = f"\n\nNew Total Debt to {user.mention} - You Owe {currency_formatter(total_owed_by_you, use_unicode)}"
    except Exception as e:
        logger.warning("Failed to fetch updated debt total after adding debt: %s", e)
        total_line = ""

    message = (f"**Added {currency_formatter(data['amount'], use_unicode)} owed to {user.mention}**{formatted_reason}"
            f"{total_line}")

    await ctx.messenger.success(
            ctx,
            title=f"{currency_formatter(data['amount'], False)} Debt Added - {config.CURRENCY_NAME} Economy Thriving",
            description=message
        )

async def handle_settle(ctx: CommandContext, user: PlatformUser, amount: str, reason: str = ""):
    debtor = int(ctx.user_id)
    creditor = int(user.id)

    if debtor == creditor:
        await handle_error(ctx, error_code="CANNOT_SETTLE_SELF")
        return
    elif str(creditor) == ctx.bot_user_id:
        await handle_error(ctx, error_code="CANNOT_SETTLE_BOT")
        return

    # Defer the response to avoid timeout
    await ctx.defer()

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
        data = await api_client.settle_debt(payload)

    except Exception as e:
        await handle_error(ctx, e, title="Error Settling Debt")
        return

    use_unicode = await fetch_unicode_preference(ctx, ctx.user_id)

    # Send confirmation message
    settled_amount = currency_formatter(data["settled_amount"], use_unicode)
    remaining_amount = currency_formatter(data["remaining_amount"], use_unicode)
    formatted_reason = f"\n*{reason}*" if reason else ""
    reverse_line = ""
    reversed_amount = data.get("auto_reversed_amount")
    if reversed_amount and Fraction(reversed_amount) != 0:
        formatted_reverse = currency_formatter(reversed_amount, use_unicode)
        reverse_line = f"\n\n**{user.mention} now owes you {formatted_reverse}** (excess auto-reversed)."
    await ctx.messenger.success(
        ctx,
        title="Debt Settled Successfully",
        description= f"Settled {settled_amount} with {user.mention}.{formatted_reason}\n\nRemaining debt: {remaining_amount}.{reverse_line}"
    )

async def handle_cashout(ctx: CommandContext, user: PlatformUser, amount: str, reason: str = ""):
    debtor = int(user.id)
    creditor = int(ctx.user_id)

    if debtor == creditor:
        await handle_error(ctx, error_code="CANNOT_SETTLE_SELF")
        return

    # Defer the response to avoid timeout
    await ctx.defer()

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
        data = await api_client.settle_debt(payload)

    except Exception as e:
        await handle_error(ctx, e, title="Error Cashing Out Debt")
        return

    use_unicode = await fetch_unicode_preference(ctx, ctx.user_id)

    # Send confirmation message
    settled_amount = currency_formatter(data["settled_amount"], use_unicode)
    remaining_amount = currency_formatter(data["remaining_amount"], use_unicode)
    formatted_reason = f"\n*{reason}*" if reason else ""
    reverse_line = ""
    reversed_amount = data.get("auto_reversed_amount")
    if reversed_amount and Fraction(reversed_amount) != 0:
        formatted_reverse = currency_formatter(reversed_amount, use_unicode)
        reverse_line = f"\n\n**You now owe {user.mention} {formatted_reverse}** (excess auto-reversed)."
    await ctx.messenger.success(
        ctx,
        title=f"{currency_formatter(data['settled_amount'], False)} Debt Cashed Out Successfully",
        description= f"Cashed out {settled_amount} from {user.mention}.{formatted_reason}\n\nRemaining debt: {remaining_amount}.{reverse_line}"
    )
