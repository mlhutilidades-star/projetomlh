import pytest
from modules.validation import normalize_cnpj, clean_cnpj, validate_cnpj, parse_valor, parse_date_br

def test_normalize_cnpj_formatted():
    """Test CNPJ normalization with formatted input"""
    result = normalize_cnpj("12345678000199")
    assert result == "12.345.678/0001-99"

def test_normalize_cnpj_already_formatted():
    """Test CNPJ normalization with already formatted input"""
    result = normalize_cnpj("12.345.678/0001-99")
    assert result == "12.345.678/0001-99"

def test_normalize_cnpj_partial():
    """Test CNPJ normalization with partial formatting"""
    result = normalize_cnpj("12.345.678000199")
    assert result == "12.345.678/0001-99"

def test_normalize_cnpj_invalid_length():
    """Test CNPJ normalization returns original when invalid length"""
    result = normalize_cnpj("12345")
    assert result == "12345"

def test_clean_cnpj():
    """Test CNPJ cleaning removes all formatting"""
    result = clean_cnpj("12.345.678/0001-99")
    assert result == "12345678000199"

def test_clean_cnpj_already_clean():
    """Test CNPJ cleaning handles already clean input"""
    result = clean_cnpj("12345678000199")
    assert result == "12345678000199"

def test_validate_cnpj_valid():
    """Test CNPJ validation accepts valid 14-digit CNPJ"""
    assert validate_cnpj("12.345.678/0001-99") is True
    assert validate_cnpj("12345678000199") is True

def test_validate_cnpj_invalid():
    """Test CNPJ validation rejects invalid CNPJ"""
    assert validate_cnpj("12345") is False
    assert validate_cnpj("") is False

def test_parse_valor_brazilian_format():
    """Test parsing Brazilian currency format"""
    result = parse_valor("R$ 1.500,00")
    assert result == 1500.00

def test_parse_valor_simple():
    """Test parsing simple currency values"""
    result = parse_valor("500,50")
    assert result == 500.50

def test_parse_valor_empty():
    """Test parsing empty values returns 0"""
    result = parse_valor("")
    assert result == 0.0

def test_parse_date_br_valid():
    """Test parsing valid Brazilian date format"""
    result = parse_date_br("31/12/2025")
    assert result is not None
    assert result.year == 2025
    assert result.month == 12
    assert result.day == 31

def test_parse_date_br_invalid():
    """Test parsing invalid date returns None"""
    result = parse_date_br("invalid-date")
    assert result is None
