from fractions import Fraction

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