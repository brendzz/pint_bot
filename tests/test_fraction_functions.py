import pytest
from fractions import Fraction
from fastapi import HTTPException
import api.fraction_functions as fractions

# Mock config values for testing
class MockConfig:
    SMALLEST_UNIT = Fraction(1, 6)
    MAXIMUM_PER_DEBT = 5

fractions.config = MockConfig  # Override the config module inside the tested module

class TestMixedNumberToFraction:
    def test_simple_fraction(self):
        assert fractions.mixed_number_to_fraction("3/4") == Fraction(3, 4)

    def test_whole_number(self):
        assert fractions.mixed_number_to_fraction("2") == Fraction(2)
        
    def test_mixed_number(self):
        assert fractions.mixed_number_to_fraction("2 1/2") == Fraction(5, 2)

    def test_mixed_number_with_extra_spaces(self):
        assert fractions.mixed_number_to_fraction("   2 1/2  ") == Fraction(5, 2)

    def test_fraction_with_spaces(self):
        assert fractions.mixed_number_to_fraction("  1/3 ") == Fraction(1, 3)

    def test_mixed_number_missing_fraction(self):
        assert fractions.mixed_number_to_fraction("2 ") == Fraction(2)

    def test_decimal(self):
        assert fractions.mixed_number_to_fraction("0.5") == Fraction(1, 2)

    def test_decimal_with_extra_spaces(self):
        assert fractions.mixed_number_to_fraction("  .5 ") == Fraction(1, 2)

    def test_zero_division(self):
        with pytest.raises(HTTPException) as e:
            fractions.mixed_number_to_fraction("1/0")
        assert e.value.detail == "INVALID_AMOUNT"

    def test_malformed_mixed_number(self):
        with pytest.raises(HTTPException) as e:
            fractions.mixed_number_to_fraction("2 3 4")
        assert e.value.detail == "INVALID_AMOUNT"

    def test_non_numeric_string(self):
        with pytest.raises(HTTPException) as e:
            fractions.mixed_number_to_fraction("hello world")
        assert e.value.detail == "INVALID_AMOUNT"

    def test_none_input(self):
        with pytest.raises(HTTPException) as e:
            fractions.mixed_number_to_fraction(None)
        assert e.value.detail == "VALIDATION_ERROR"

    def test_empty_string(self):
        with pytest.raises(HTTPException) as e:
            fractions.mixed_number_to_fraction("")
        assert e.value.detail == "INVALID_AMOUNT"

    def test_whitespace_only(self):
        with pytest.raises(HTTPException) as e:
            fractions.mixed_number_to_fraction("   ")
        assert e.value.detail == "INVALID_AMOUNT"
