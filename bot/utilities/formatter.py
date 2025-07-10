"""Formatter module for converting fractions and formatting currency."""
from fractions import Fraction
import bot.config as config
from bot.utilities.fraction_list import UNICODE_FRACTIONS, SUPERSCRIPT, SUBSCRIPT

def fraction_to_unicode(fraction_str: str) -> str:
    """
    Convert a fraction in string form to its Unicode representation.

    Args:
        fraction_str (str): The fraction as a string (e.g., "1/6", "7/8").

    Returns:
        str: The Unicode representation of the fraction, or a custom Unicode string if no default exists.
    """
    try:
        # Normalize the fraction to its simplest form
        fraction = Fraction(fraction_str)
        simplified_str = f"{fraction.numerator}/{fraction.denominator}"

        # Check if the fraction has a default Unicode representation
        if simplified_str in UNICODE_FRACTIONS:
            return UNICODE_FRACTIONS[simplified_str]
        else:
            # Create a custom Unicode fraction
            return custom_unicode_fraction(fraction)
    except ValueError:
        # If the input is invalid, return it as-is
        return fraction_str

def to_superscript(number: int) -> str:
    """Convert a number to its superscript representation."""
    return ''.join(SUPERSCRIPT.get(char, char) for char in str(number))

def to_subscript(number: int) -> str:
    """Convert a number to its subscript representation."""
    return ''.join(SUBSCRIPT.get(char, char) for char in str(number))

def custom_unicode_fraction(fraction: Fraction) -> str:
    """
    Create a custom Unicode fraction string if no default Unicode representation exists.

    Args:
        fraction (Fraction): The fraction to convert.

    Returns:
        str: The custom Unicode fraction string.
    """
    numerator = to_superscript(fraction.numerator)
    denominator = to_subscript(fraction.denominator)
    return f"{numerator}/{denominator}"

def to_percentage(part, whole, decimal_places) -> str:
    """Divides two numbers and returns a percentage representation."""
    fraction = Fraction(part) / Fraction(whole)
    percentage = fraction * 100
    return f"({percentage:.{decimal_places}f}%)"

def with_conversion_currency(value, string_amount) -> str:
    value = Fraction(value)
    ratio = Fraction(config.EXCHANGE_RATE_TO_CONVERSION_CURRENCY)
    converted = ratio * value
    if config.CONVERSION_CURRENCY_SHOW_SYMBOL_BEFORE_AMOUNT:
        formatted = f"{string_amount} [{config.CONVERSION_CURRENCY}{converted}]"
    else:
        formatted = f"{string_amount} [{converted}{config.CONVERSION_CURRENCY}]"
    return formatted

def with_emoji_visuals(value, string_amount, new_line = True) -> str:
    value = round(Fraction(value))
    emojis = config.CURRENCY_DISPLAY_EMOJI*value
    formatted = f"{string_amount}{"\n" if new_line else ""}{emojis}"
    return formatted

def currency_formatter(amount, use_unicode: bool=False) -> str:
    """Format the currency amount based on the configuration."""
    fraction = Fraction(amount)

    # Check if the number is singular or plural
    if fraction > 0 and fraction <= 1:
        currency = config.CURRENCY_NAME.lower()
    else:
        currency = config.CURRENCY_NAME_PLURAL.lower()

    if config.USE_DECIMAL_OUTPUT is True:
        return f"{float(fraction)} {currency}"
    else:
        # Get the whole number part
        whole_number = fraction.numerator // fraction.denominator
        # Get the remainder (numerator of the fractional part)
        remainder = fraction.numerator % fraction.denominator

        # If there's no fractional part, return the whole number
        if remainder == 0:
            return f"{whole_number} {currency}"

        # Calculate the fractional part
        fractional_part = Fraction(remainder, fraction.denominator)

    final_fraction = fraction_to_unicode(str(fractional_part)) if use_unicode else f"{remainder}/{fraction.denominator}"
    if whole_number == 0:
        return f"{final_fraction} {currency}"
    return f"{whole_number} {final_fraction} {currency}"
