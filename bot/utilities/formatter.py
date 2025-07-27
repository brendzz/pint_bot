"""Formatter module for converting fractions and formatting currency."""
from fractions import Fraction
from datetime import datetime
from dateutil import parser
import bot.config as config
from bot.utilities.fraction_list import UNICODE_FRACTIONS, SUPERSCRIPT, SUBSCRIPT

def format_date(date_str: str, normalise_for_api: bool = False) -> str:
    """
    Format into specified date format
    """
    try:
        if normalise_for_api:
            parsed_date = parser.parse(date_str, dayfirst=True)  # allows dd-mm-yyyy
            return parsed_date.strftime("%Y-%m-%d")
        else:
            parsed_date = parser.parse(date_str)
            return parsed_date.strftime(config.DATE_FORMAT)
    except (ValueError, TypeError):
        return "Invalid date"

def sanitize_dates(start_date, end_date):
    if start_date is not None:
        start_date = format_date(start_date, True)
    if end_date is not None:
        end_date = format_date(end_date, True)
    return start_date, end_date

def should_display_as_settle(transaction_type: str, display_as_settle: bool) -> bool:
    return False if transaction_type and transaction_type.strip().lower() == "cashout" else display_as_settle

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

def with_percentage(value: Fraction, total: Fraction, string_amount:str) -> str:
    """Format a debt with its percentage of the total."""
    formatted = f"{string_amount} {to_percentage(value, total, config.PERCENTAGE_DECIMAL_PLACES)}"
    return formatted

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
    total_amount = sum(Fraction(entry['amount']) for entry in entries)
    lines = [format_amount(
        total_amount, total, use_unicode,
        show_percentages, show_conversion_currency, show_emoji_visuals, emoji_on_total=True
    )]

    if show_details:
        for entry in entries:
            amount = format_amount(
                entry["amount"], total, use_unicode,
                show_percentages, show_conversion_currency, show_emoji_visuals, emoji_on_total=False
            )
            reason = entry['reason'] or "[No Reason Given]"
            lines.append(f"- {amount} for *{reason}* on {format_date(entry['timestamp'])}")
    return lines

def format_overall_debts(
    total_owed: Fraction,
    show_conversion_currency: bool,
    show_emoji_visuals: bool,
    use_unicode: bool,
    use_upper_case: bool = True
):
    formatted_amount = format_amount(
        total_owed, total_owed, use_unicode,
        False, show_conversion_currency, show_emoji_visuals, emoji_on_total=True
    )
    if (use_upper_case):
        return formatted_amount.upper()
    else:
        return formatted_amount

def format_amount(
    value,
    total,
    use_unicode,
    show_percentages,
    show_conversion_currency,
    show_emoji_visuals,
    emoji_on_total=True
):
    amt = currency_formatter(value, use_unicode)
    if show_conversion_currency:
        amt = with_conversion_currency(value, amt)
    if show_percentages:
        amt = with_percentage(value, total, amt)
    if show_emoji_visuals:
        amt = with_emoji_visuals(value, amt, emoji_on_total)
    return amt