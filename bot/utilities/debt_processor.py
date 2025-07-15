from bot.utilities.formatter import currency_formatter, with_conversion_currency, with_emoji_visuals
from fractions import Fraction

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
        return("\nPerfectly balanced!")