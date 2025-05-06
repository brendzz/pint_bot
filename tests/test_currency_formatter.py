from currency_formatter import currency_formatter

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