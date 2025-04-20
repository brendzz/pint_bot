from fractions import Fraction
from fraction_list import UNICODE_FRACTIONS

# Format pints
def currency_formatter(pint_number, use_unicode=False) -> str:
    # Convert pint_number to a Fraction
    fraction = Fraction(pint_number)
    
    # Check if the number is singular or plural
    if fraction > 0 and fraction <= 1:
        pints = "pint"
    else:
        pints = "pints"
    
    # Get the whole number part
    whole_number = fraction.numerator // fraction.denominator
    # Get the remainder (numerator of the fractional part)
    remainder = fraction.numerator % fraction.denominator

    # If there's no fractional part, return the whole number
    if remainder == 0:
        return f"{whole_number} {pints}"

    # Calculate the fractional part
    fractional_part = Fraction(remainder, fraction.denominator)

    # If there's no whole number part, return just the fraction
    if whole_number == 0:
        if use_unicode:
            final_fraction = UNICODE_FRACTIONS.get(fractional_part, f"{remainder}/{fraction.denominator}")
        else:
            final_fraction = f"{remainder}/{fraction.denominator}"
        return f"{final_fraction} {pints}"

    # Otherwise, return the mixed number
    # Otherwise, return the mixed number
    if use_unicode:
        final_fraction = UNICODE_FRACTIONS.get(fractional_part, f"{remainder}/{fraction.denominator}")
    else:
        final_fraction = f"{remainder}/{fraction.denominator}"
    return f"{whole_number} {final_fraction} {pints}"