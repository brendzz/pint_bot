from fractions import Fraction
from fraction_formatter import (
    fraction_to_unicode,
    to_superscript,
    to_subscript,
    custom_unicode_fraction
)

def test_fraction_to_unicode_known_fraction():
    assert fraction_to_unicode("1/2") == "½"

def test_fraction_to_unicode_custom_fraction():
    result = fraction_to_unicode("3/7")
    assert result == "³/₇"

def test_fraction_to_unicode_invalid_input():
    assert fraction_to_unicode("abc") == "abc"

def test_to_superscript():
    assert to_superscript(123) == "¹²³"

def test_to_subscript():
    assert to_subscript(456) == "₄₅₆"

def test_custom_unicode_fraction():
    f = Fraction(5, 9)
    assert custom_unicode_fraction(f) == "⁵/₉"
