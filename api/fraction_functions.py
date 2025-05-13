"""Module for fraction conversion functions."""
from fractions import Fraction
from fastapi import HTTPException
import api.config as config

def mixed_number_to_fraction(input_str: str) -> Fraction:
    """Function to convert a mixed number or fraction string to a Fraction object
    
    Raises:
        HTTPException: with appropriate error detail if the input is invalid.
    """
    if input_str is None:
        raise HTTPException(status_code=400, detail="VALIDATION_ERROR")
    
    try:
        # Split the input into whole number and fractional part
        input_str = input_str.strip()

        if " " in input_str:
            whole_str, fraction_str = input_str.split()
            whole = int(whole_str)
            numerator, denominator = map(int, fraction_str.split("/"))
        elif "/" in input_str:
            whole = 0
            numerator, denominator = map(int, input_str.split("/"))
        else:
            return Fraction(int(input_str))

        if denominator == 0:
            raise HTTPException(status_code=400, detail="INVALID_AMOUNT")

        return Fraction(whole * denominator + numerator, denominator)

    except (ValueError, ZeroDivisionError) as exc:
        raise HTTPException(status_code=400, detail="INVALID_AMOUNT") from exc
    except TypeError as exc:
        raise HTTPException(status_code=400, detail="VALIDATION_ERROR") from exc

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
