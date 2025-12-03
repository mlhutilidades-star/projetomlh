import pytest
from unittest.mock import Mock, patch
from modules.rules import get_rule_for_cnpj

@patch('modules.rules.database.get_regra')
def test_get_rule_for_cnpj_active(mock_get_regra):
    """Test retrieving active rule for CNPJ"""
    mock_get_regra.return_value = {
        'cnpj': '12.345.678/0001-99',
        'categoria': 'Fornecedor A',
        'ativo': True
    }
    
    result = get_rule_for_cnpj('12.345.678/0001-99')
    
    assert result is not None
    assert result['cnpj'] == '12.345.678/0001-99'
    assert result['ativo'] is True
    assert mock_get_regra.called

@patch('modules.rules.database.get_regra')
def test_get_rule_for_cnpj_inactive(mock_get_regra):
    """Test that inactive rules are not returned"""
    mock_get_regra.return_value = {
        'cnpj': '12.345.678/0001-99',
        'categoria': 'Fornecedor B',
        'ativo': False
    }
    
    result = get_rule_for_cnpj('12.345.678/0001-99')
    
    assert result is None

@patch('modules.rules.database.get_regra')
def test_get_rule_for_cnpj_not_found(mock_get_regra):
    """Test handling when no rule exists"""
    mock_get_regra.return_value = None
    
    result = get_rule_for_cnpj('99.999.999/0001-99')
    
    assert result is None
