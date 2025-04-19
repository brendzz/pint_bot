from fractions import Fraction

# Format pints
def pint_formatter(pint_number) ->str:
    # Convert pint_number to a Fraction
    fraction = Fraction(pint_number)
    
    # Check if the number is singular or plural
    if fraction <= 1:
        pints="pint"
    else:
        pints="pints"
    
    # Get the whole number part
    whole_number = fraction.numerator // fraction.denominator
    # Get the remainder (numerator of the fractional part)
    remainder = fraction.numerator % fraction.denominator

    # If there's no fractional part, return the whole number
    if remainder == 0:
        return f"{whole_number} {pints}"

    # If there's no whole number part, return just the fraction
    if whole_number == 0:
        return f"{remainder}/{fraction.denominator} {pints}"

    # Otherwise, return the mixed number
    return f"{whole_number} {remainder}/{fraction.denominator} {pints}"