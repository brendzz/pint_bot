from fractions import Fraction
from fraction_formatter import fraction_to_unicode

# Format pints
def currency_formatter(amount, config: dict[str, any], use_unicode: bool=False) -> str:
    # Convert pint_number to a Fraction
    fraction = Fraction(amount)
    
    # Check if the number is singular or plural
    if fraction > 0 and fraction <= 1:
        currency = config["CURRENCY_NAME"].lower()
    else:
        currency = config["CURRENCY_NAME_PLURAL"].lower()
    
    if config["USE_DECIMAL_OUTPUT"] == True:
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

        if whole_number == 0:
                final_fraction = (
                    fraction_to_unicode(fractional_part) if use_unicode else f"{remainder}/{fraction.denominator}"
                )
                return f"{final_fraction} {currency}"

        # Otherwise, return the mixed number
        final_fraction = (
            fraction_to_unicode(fractional_part) if use_unicode else f"{remainder}/{fraction.denominator}"
        )
        return f"{whole_number} {final_fraction} {currency}"