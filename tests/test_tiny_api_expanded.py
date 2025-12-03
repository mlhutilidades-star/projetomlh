import pytest
from unittest.mock import Mock, patch
from modules.tiny_api import (
    listar_produtos, 
    obter_produto_por_sku, 
    obter_produto_detalhado,
    atualizar_preco_custo
)
from modules import config

@patch('modules.tiny_api.requests.get')
def test_listar_produtos_pagination(mock_get):
    """Test product listing with pagination"""
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        'retorno': {
            'status': 'OK',
            'numero_paginas': 3,
            'pagina': 1,
            'produtos': [
                {'produto': {'id': str(i), 'codigo': f'PROD{i:03d}', 'nome': f'Produto {i}'}}
                for i in range(1, 101)
            ]
        }
    }
    mock_get.return_value = mock_response
    
    with patch.object(config, 'TINY_API_TOKEN', 'test_token'):
        result = listar_produtos(page=1, pesquisa="")
        
        assert 'retorno' in result
        assert result['retorno']['numero_paginas'] == 3
        assert len(result['retorno']['produtos']) == 100

@patch('modules.tiny_api.requests.get')
def test_obter_produto_por_sku_multiple_results(mock_get):
    """Test product fetch when multiple results returned"""
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        'retorno': {
            'produtos': [
                {'produto': {'codigo': 'SKU001', 'nome': 'First Match', 'preco': '10,00'}},
                {'produto': {'codigo': 'SKU001-A', 'nome': 'Second Match', 'preco': '15,00'}}
            ]
        }
    }
    mock_get.return_value = mock_response
    
    with patch.object(config, 'TINY_API_TOKEN', 'test_token'):
        result = obter_produto_por_sku('SKU001')
        
        # Should return first match
        assert result['codigo'] == 'SKU001'
        assert result['nome'] == 'First Match'

@patch('modules.tiny_api.requests.post')
def test_atualizar_preco_custo_success(mock_post):
    """Test successful cost price update"""
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.text = '{"retorno": {"status": "OK"}}'
    mock_response.headers = {}
    mock_response.json.return_value = {
        'retorno': {
            'status': 'OK',
            'registros': [{'registro': {'id': '123'}}]
        }
    }
    mock_post.return_value = mock_response
    
    with patch.object(config, 'TINY_API_TOKEN', 'test_token'):
        result = atualizar_preco_custo('PROD001', 150.00)
        
        assert result['ok'] is True
        assert result['status_code'] == 200
        assert result['data']['retorno']['status'] == 'OK'

@patch('modules.tiny_api.requests.post')
def test_atualizar_preco_custo_retry(mock_post):
    """Test cost price update with retry on failure"""
    # First call fails, second succeeds
    mock_fail = Mock()
    mock_fail.status_code = 500
    mock_fail.text = '{"error": "Server error"}'
    mock_fail.headers = {}
    mock_fail.json.return_value = {'error': 'Server error'}
    
    mock_success = Mock()
    mock_success.status_code = 200
    mock_success.text = '{"retorno": {"status": "OK"}}'
    mock_success.headers = {}
    mock_success.json.return_value = {
        'retorno': {'status': 'OK'}
    }
    
    mock_post.side_effect = [mock_fail, mock_success]
    
    with patch.object(config, 'TINY_API_TOKEN', 'test_token'):
        result = atualizar_preco_custo('PROD001', 150.00, max_retries=2)
        
        # Should succeed on retry
        assert result['ok'] is True
        assert result['data']['retorno']['status'] == 'OK'
        assert mock_post.call_count == 2

@patch('modules.tiny_api.requests.get')
def test_obter_produto_detalhado_fields(mock_get):
    """Test detailed product fetch returns all expected fields"""
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        'retorno': {
            'produto': {
                'codigo': 'DETAIL001',
                'nome': 'Produto Detalhado',
                'preco': '199,99',
                'preco_custo': '100,00',
                'unidade': 'UN',
                'peso_liquido': '1.5',
                'ncm': '12345678'
            }
        }
    }
    mock_get.return_value = mock_response
    
    with patch.object(config, 'TINY_API_TOKEN', 'test_token'):
        result = obter_produto_detalhado('DETAIL001')
        
        assert result['codigo'] == 'DETAIL001'
        assert result['preco'] == 199.99
        assert result['preco_custo'] == 100.00
        assert 'raw' in result
        assert result['raw']['ncm'] == '12345678'
