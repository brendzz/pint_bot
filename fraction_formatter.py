from fractions import Fraction
from fraction_list import UNICODE_FRACTIONS, SUPERSCRIPT, SUBSCRIPT

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