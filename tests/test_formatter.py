from fractions import Fraction

import pytest
from formatter import currency_formatter, custom_unicode_fraction, fraction_to_unicode, to_percentage, to_subscript, to_superscript


MOCK_CONFIG = {
    "CURRENCY_NAME": "Pint",
    "CURRENCY_NAME_PLURAL": "Pints",
    "USE_DECIMAL_OUTPUT": False
}

def test_singular_fraction():
    assert currency_formatter("1", MOCK_CONFIG) == "1 pint"

def test_plural_whole_number():
    assert currency_formatter("2", MOCK_CONFIG) == "2 pints"

def test_simple_fraction():
    assert currency_formatter("1/2", MOCK_CONFIG) == "1/2 pint"

def test_mixed_fraction():
    assert currency_formatter("5/2", MOCK_CONFIG) == "2 1/2 pints"

def test_unicode_fraction():
    result = currency_formatter("3/2", MOCK_CONFIG, use_unicode=True)
    assert result.startswith("1 ") and "½" in result

def test_unicode_single_fraction():
    result = currency_formatter("1/4", MOCK_CONFIG, use_unicode=True)
    assert "¼" in result

def test_zero_value():
    assert currency_formatter("0", MOCK_CONFIG) == "0 pints"

def test_decimal_output():
    decimal_config = MOCK_CONFIG.copy()
    decimal_config["USE_DECIMAL_OUTPUT"] = True
    assert currency_formatter("3/2", decimal_config) == "1.5 pints"
    assert currency_formatter("1", decimal_config) == "1.0 pint"

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