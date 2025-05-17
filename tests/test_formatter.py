from fractions import Fraction
from unittest.mock import patch

import pytest
from bot.utilities.formatter import currency_formatter, custom_unicode_fraction, fraction_to_unicode, to_percentage, to_subscript, to_superscript

class TestCurrencyFormatter:
    def test_singular_fraction(self):
        assert currency_formatter("1") == "1 testcoin"

    def test_plural_whole_number(self):
        assert currency_formatter("2") == "2 testcoins"

    def test_simple_fraction(self):
        assert currency_formatter("1/2") == "1/2 testcoin"

    def test_mixed_fraction(self):
        assert currency_formatter("5/2") == "2 1/2 testcoins"

    def test_unicode_fraction(self):
        result = currency_formatter("3/2", True)
        assert result.startswith("1 ") and "½" in result

    def test_unicode_single_fraction(self):
        result = currency_formatter("1/4", True)
        assert "¼" in result

    def test_zero_value(self):
        assert currency_formatter("0") == "0 testcoins"

    @patch("bot.config.USE_DECIMAL_OUTPUT", True)
    def test_decimal_output(self):
        assert currency_formatter("3/2") == "1.5 testcoins"
        assert currency_formatter("1") == "1.0 testcoin"

class TestFractionToUnicode:
    def test_fraction_to_unicode_known_fraction(self):
        assert fraction_to_unicode("1/2") == "½"
        assert fraction_to_unicode("1/4") == "¼"
        assert fraction_to_unicode("3/4") == "¾"
        assert fraction_to_unicode("1/3") == "⅓"
        assert fraction_to_unicode("2/3") == "⅔"

    def test_fraction_to_unicode_custom_fraction(self):
        result = fraction_to_unicode("3/7")
        assert result == "³/₇"

    def test_fraction_to_unicode_invalid_input(self):
        assert fraction_to_unicode("abc") == "abc"
        assert fraction_to_unicode("") == ""

    def test_fraction_to_unicode_simplifies(self):
        assert fraction_to_unicode("2/4") == "½"
        assert fraction_to_unicode("10/20") == "½"

    def test_fraction_to_unicode_negative_fraction(self):
        result = fraction_to_unicode("-1/5")
        assert result.startswith("⁻")

class TestToSuperscript:
    def test_to_superscript(self):
        assert to_superscript(123) == "¹²³"

class TestToSubscript:
    def test_to_subscript(self):
        assert to_subscript(456) == "₄₅₆"

class TestCustomUnicodeFraction:
    def test_custom_unicode_fraction(self):
        f = Fraction(5, 9)
        assert custom_unicode_fraction(f) == "⁵/₉"

    def test_custom_unicode_fraction_negative(self):
        f = Fraction(-3, 7)
        assert custom_unicode_fraction(f).startswith("⁻")

class TestToPercentage:
    def test_basic_percentage(self):
        assert to_percentage(25, 100, 0) == "25%"

    def test_decimal_places(self):
        assert to_percentage(1, 3, 2) == "33.33%"

    def test_zero_part(self):
        assert to_percentage(0, 10, 1) == "0.0%"

    def test_fraction_inputs(self):
        result = to_percentage(Fraction(1, 4), Fraction(1, 2), 3)
        assert result == "50.000%"

    def test_whole_equals_part(self):
        assert to_percentage(5, 5, 1) == "100.0%"

    def test_large_numbers(self):
        assert to_percentage(2000, 8000, 2) == "25.00%"

    def test_zero_division_handling(self):
        with pytest.raises(ZeroDivisionError):
            to_percentage(5, 0, 1)