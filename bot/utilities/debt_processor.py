from bot.utilities.formatter import currency_formatter, with_conversion_currency, with_emoji_visuals
from fractions import Fraction

def find_net_difference(owed_to_you: Fraction,
        owed_by_you: Fraction,
        use_unicode: bool = None,
        show_conversion_currency: bool = None,
        show_emoji_visuals: bool = None,
        individual_user: bool = True,
        emphasis: bool = True) -> str:
    
    net_difference = owed_to_you - owed_by_you
    net_difference_formatted = currency_formatter(abs(net_difference), use_unicode)
    if show_conversion_currency:
         net_difference_formatted = with_conversion_currency(net_difference, net_difference_formatted)
    if show_emoji_visuals:
         net_difference_formatted = with_emoji_visuals(net_difference, net_difference_formatted)

    
    if net_difference>0:
        message_start = f"\nNet Difference - {'Owed To You' if individual_user else 'Added To Economy'}: {net_difference_formatted}"
        message_end = f"\n{'You' if individual_user else 'Transactions in this period'} are in the positive!"
    elif net_difference<0:
        message_start = f"\nNet Difference - {'You Owe' if individual_user else 'Cashed out of Economy'}: {net_difference_formatted}"
        message_end = f"\n{'You' if individual_user else 'Transactions in this period'} are in the negative!"
    else:
        message_start = "\nYou owe as much as you are owed."
        message_end = "Perfectly balanced!"
    
    if emphasis:
        message_start = f"__**{message_start.upper()}**__"

    message = message_start  + message_end
    return message