from fractions import Fraction
import pytest
from fraction_formatter import (
    fraction_to_unicode,
    to_percentage,
    to_superscript,
    to_subscript,
    custom_unicode_fraction
)

def test_fraction_to_unicode_known_fraction():
    assert fraction_to_unicode("1/2") == "½"
    assert fraction_to_unicode("1/4") == "¼"
    assert fraction_to_unicode("3/4") == "¾"
    assert fraction_to_unicode("1/3") == "⅓"
    assert fraction_to_unicode("2/3") == "⅔"

def test_fraction_to_unicode_custom_fraction():
    result = fraction_to_unicode("3/7")
    assert result == "³/₇"

def test_fraction_to_unicode_invalid_input():
    assert fraction_to_unicode("abc") == "abc"
    assert fraction_to_unicode("") == ""

def test_fraction_to_unicode_simplifies():
    assert fraction_to_unicode("2/4") == "½"
    assert fraction_to_unicode("10/20") == "½"

def test_fraction_to_unicode_negative_fraction():
    result = fraction_to_unicode("-1/5")
    assert result.startswith("⁻")

def test_to_superscript():
    assert to_superscript(123) == "¹²³"

def test_to_subscript():
    assert to_subscript(456) == "₄₅₆"

def test_custom_unicode_fraction():
    f = Fraction(5, 9)
    assert custom_unicode_fraction(f) == "⁵/₉"

def test_custom_unicode_fraction_negative():
    f = Fraction(-3, 7)
    assert custom_unicode_fraction(f).startswith("⁻")

def test_basic_percentage():
    config = {"PERCENTAGE_DECIMAL_PLACES": 0}
    assert to_percentage(25, 100, config) == "25%"

def test_decimal_places():
    config = {"PERCENTAGE_DECIMAL_PLACES": 2}
    assert to_percentage(1, 3, config) == "33.33%"

def test_zero_part():
    config = {"PERCENTAGE_DECIMAL_PLACES": 1}
    assert to_percentage(0, 10, config) == "0.0%"

def test_fraction_inputs():
    config = {"PERCENTAGE_DECIMAL_PLACES": 3}
    result = to_percentage(Fraction(1, 4), Fraction(1, 2), config)
    assert result == "50.000%"

def test_whole_equals_part():
    config = {"PERCENTAGE_DECIMAL_PLACES": 1}
    assert to_percentage(5, 5, config) == "100.0%"

def test_large_numbers():
    config = {"PERCENTAGE_DECIMAL_PLACES": 2}
    assert to_percentage(2000, 8000, config) == "25.00%"

def test_zero_division_handling():
    config = {"PERCENTAGE_DECIMAL_PLACES": 1}
    with pytest.raises(ZeroDivisionError):
        to_percentage(5, 0, config)