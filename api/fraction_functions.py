"""Module for fraction conversion functions."""
from fractions import Fraction
from fastapi import HTTPException
import api.config as config

def mixed_number_to_fraction(input_str: str) -> Fraction:
    """Function to convert a mixed number or fraction string to a Fraction object"""
    try:
        return Fraction(input_str)
    except ValueError:
        # Split the input into whole number and fractional part
        try:
            if " " in input_str:
                whole, fraction_part = input_str.split()
                whole = int(whole)
                numerator, denominator = map(int, fraction_part.split("/"))
            else:
                # If there's no whole number, treat it as a simple fraction
                whole = 0
                numerator, denominator = map(int, input_str.split("/"))
        except (ValueError, ZeroDivisionError) as exc:
            raise HTTPException(status_code=400, detail="INVALID_AMOUNT") from exc
        except Exception as exc:
            raise HTTPException(status_code=400, detail="BAD_REQUEST") from exc

        return Fraction(whole * denominator + numerator, denominator)

def check_quantization(amount: Fraction):
    """Check if the fraction is quantized to the smallest unit using modulo"""
    if amount % config.SMALLEST_UNIT != 0:
        raise HTTPException(
            status_code=400,
            detail="NOT_QUANTIZED"
        )

def check_in_range(amount: Fraction, settling: bool = False):
    """Check if the amount is within the allowed range"""
    if amount < 0:
        raise HTTPException(status_code=400, detail="NEGATIVE_AMOUNT")
    if amount == 0:
        raise HTTPException(status_code=400, detail="ZERO_AMOUNT")
    if not settling and amount > Fraction(config.MAXIMUM_PER_DEBT):
        raise HTTPException(status_code=400, detail="EXCEEDS_MAXIMUM")
