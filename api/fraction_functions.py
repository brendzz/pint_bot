"""Module for fraction conversion functions."""
from fractions import Fraction
import re
from fastapi import HTTPException
import api.config as config

# Accepts: "3", "-3", "2.5", ".5", "7/3", "-7/3", "2 1/3", "-2 1/3"
# Rejects: "3 -1/2", "2 7/3", "1_000", "1e3", "1/0", "", "abc"
_PLAIN_NUMBER = re.compile(r"^-?(\d+(\.\d+)?|\.\d+)$")
_SIMPLE_FRACTION = re.compile(r"^(-?)(\d+)/(\d+)$")
_MIXED_NUMBER = re.compile(r"^(-?)(\d+)\s+(\d+)/(\d+)$")

def mixed_number_to_fraction(input_str: str) -> Fraction:
    """Function to convert a mixed number or fraction string to a Fraction object

    Raises:
        HTTPException: with appropriate error detail if the input is invalid.
    """
    if input_str is None:
        raise HTTPException(status_code=400, detail="VALIDATION_ERROR")

    input_str = input_str.strip()

    # Plain number (integer or decimal)
    if _PLAIN_NUMBER.match(input_str):
        return Fraction(input_str)

    # Simple fraction, e.g. "7/3" (improper fractions are allowed)
    simple = _SIMPLE_FRACTION.match(input_str)
    if simple:
        sign, numerator, denominator = simple.groups()
        den = int(denominator)
        if den == 0:
            raise HTTPException(status_code=400, detail="INVALID_AMOUNT")
        numerator = int(numerator)
        return Fraction(-numerator if sign == "-" else numerator, den)

    # Mixed number, e.g. "2 1/3" — the fractional part must be a proper fraction
    mixed = _MIXED_NUMBER.match(input_str)
    if mixed:
        sign, whole_str, numerator_str, denominator_str = mixed.groups()
        den = int(denominator_str)
        num = int(numerator_str)
        if den == 0:
            raise HTTPException(status_code=400, detail="INVALID_AMOUNT")
        if num >= den:
            raise HTTPException(status_code=400, detail="INVALID_AMOUNT")
        value = Fraction(int(whole_str) * den + num, den)
        return -value if sign == "-" else value

    raise HTTPException(status_code=400, detail="INVALID_AMOUNT")

def check_quantization(amount: Fraction):
    """Check if the fraction is quantized to the smallest unit using modulo"""
    if amount % config.SMALLEST_UNIT != 0:
        raise HTTPException(status_code=400, detail="NOT_QUANTIZED")

def check_in_range(amount: Fraction, settling: bool = False):
    """Check if the amount is within the allowed range"""
    if amount < 0:
        raise HTTPException(status_code=400, detail="NEGATIVE_AMOUNT")
    if amount == 0:
        raise HTTPException(status_code=400, detail="ZERO_AMOUNT")
    if not settling and amount > Fraction(config.MAXIMUM_PER_DEBT):
        raise HTTPException(status_code=400, detail="EXCEEDS_MAXIMUM")
