from dateutil.parser import isoparse
from fractions import Fraction
from bot.utilities.formatter import format_overall_debts
from bot.utilities.user_utils import get_display_name

def build_transaction_line(tx, time_str, amount, debtor, creditor, tx_type, display_as_settle):
    reason = tx.get('reason', '')
    line = ""

    if tx_type == "Owe":
        line = f"`{time_str}`: **Owe:** {amount} owed from {debtor} to {creditor}"
    elif tx_type == "Settle":
        if display_as_settle:
            line = f"`{time_str}`: **Settle:** {amount} settled from {debtor} to {creditor}"
        else:
            line = f"`{time_str}`: **Cashout:** {amount} cashed out by {creditor} from {debtor}"

    if reason:
        line += f" *({reason})*"

    return line


async def process_transaction(tx, config, interaction, show_conversion_currency, show_emoji_visuals, use_unicode, display_as_settle):
    dt = isoparse(tx['timestamp'])
    date_str = dt.strftime(config.DATE_FORMAT)
    time_str = dt.strftime(config.TIME_FORMAT)

    tx_type = tx['type'].capitalize()
    fraction_amount = Fraction(tx['amount'])

    amount = format_overall_debts(fraction_amount, show_conversion_currency, show_emoji_visuals, use_unicode, False)
    debtor = await get_display_name(interaction.client, tx['debtor'])
    creditor = await get_display_name(interaction.client, tx['creditor'])

    line = build_transaction_line(tx, time_str, amount, debtor, creditor, tx_type, display_as_settle)
    return date_str, tx_type, fraction_amount, line