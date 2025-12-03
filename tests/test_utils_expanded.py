import pytest
from modules.utils import format_currency, clean_cnpj

def test_format_currency():
    """Test currency formatting"""
    result = format_currency(1500.00)
    assert "R$" in result
    assert "1.500,00" in result

def test_clean_cnpj():
    """Test CNPJ cleaning"""
    result = clean_cnpj("12.345.678/0001-99")
    assert result == "12345678000199"

def test_clean_cnpj_empty():
    """Test CNPJ cleaning with empty input"""
    result = clean_cnpj("")
    assert result == ""
    result = clean_cnpj(None)
    assert result == ""
