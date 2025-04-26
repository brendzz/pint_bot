from fractions import Fraction

# Function to convert a mixed number or fraction string to a Fraction object
def mixed_number_to_fraction(input_str: str) -> Fraction:

    try:
        return Fraction(input_str)
    except ValueError:
        # Split the input into whole number and fractional part
        if " " in input_str:
            whole, fraction_part = input_str.split()
            whole = int(whole)
            numerator, denominator = map(int, fraction_part.split("/"))
        else:
            # If there's no whole number, treat it as a simple fraction
            whole = 0
            numerator, denominator = map(int, input_str.split("/"))

        return Fraction(whole * denominator + numerator, denominator)

# Function to calcualte the allowed denominators for Fractions based on the minimum allowed size 
# E.g. [1, 2, 3, 6] for 1/6
"""
def calculate_allowed_denominators(minimum_unit: str) -> list:
    min_unit = Fraction(minimum_unit)
    denominator = min_unit.denominator

    # Find all divisors of the denominator
    allowed_denominators = [i for i in range(1, denominator + 1) if denominator % i == 0]
    return allowed_denominators
    """
