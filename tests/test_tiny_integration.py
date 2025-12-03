import pytest
from unittest.mock import Mock, patch
from modules.tiny_api import listar_produtos, obter_produto_por_sku, obter_produto_detalhado
from modules import config

@patch('modules.tiny_api.requests.get')
def test_listar_produtos_success(mock_get):
    """Test product listing with mocked successful Tiny API response"""
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        'retorno': {
            'status_processamento': '3',
            'status': 'OK',
            'numero_paginas': 1,
            'produtos': [
                {'produto': {'id': '123', 'codigo': 'PROD001', 'nome': 'Produto Teste 1'}},
                {'produto': {'id': '124', 'codigo': 'PROD002', 'nome': 'Produto Teste 2'}}
            ]
        }
    }
    mock_get.return_value = mock_response
    
    with patch.object(config, 'TINY_API_TOKEN', 'test_token_12345'):
        result = listar_produtos(page=1, pesquisa="Teste")
        
        assert mock_get.called
        assert 'retorno' in result
        assert len(result['retorno']['produtos']) == 2

@patch('modules.tiny_api.requests.get')
def test_listar_produtos_timeout(mock_get):
    """Test product listing handles timeout gracefully"""
    mock_get.side_effect = Exception('Timeout')
    
    with patch.object(config, 'TINY_API_TOKEN', 'test_token'):
        result = listar_produtos(page=1, pesquisa="")
        
        assert 'error' in result
        assert result['retorno']['produtos'] == []

def test_listar_produtos_no_token():
    """Test that missing token returns error"""
    with patch.object(config, 'TINY_API_TOKEN', None):
        result = listar_produtos(page=1, pesquisa="")
        
        assert 'error' in result
        assert 'Token não configurado' in result['error']

@patch('modules.tiny_api.requests.get')
def test_obter_produto_por_sku_success(mock_get):
    """Test fetching product by SKU with mocked response"""
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        'retorno': {
            'produtos': [
                {
                    'produto': {
                        'codigo': 'SKU123',
                        'nome': 'Produto SKU Teste',
                        'preco': '99,90',  # Tiny API retorna com vírgula
                        'preco_custo': '50,00'
                    }
                }
            ]
        }
    }
    mock_get.return_value = mock_response
    
    with patch.object(config, 'TINY_API_TOKEN', 'test_token'):
        result = obter_produto_por_sku('SKU123')
        
        assert 'error' not in result
        assert result['codigo'] == 'SKU123'
        assert result['nome'] == 'Produto SKU Teste'
        assert result['preco'] == 99.90
        assert result['preco_custo'] == 50.00

@patch('modules.tiny_api.requests.get')
def test_obter_produto_por_sku_not_found(mock_get):
    """Test product not found by SKU returns error"""
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        'retorno': {
            'produtos': []
        }
    }
    mock_get.return_value = mock_response
    
    with patch.object(config, 'TINY_API_TOKEN', 'test_token'):
        result = obter_produto_por_sku('NONEXISTENT')
        
        assert 'error' in result
        assert 'não encontrado' in result['error'].lower()

@patch('modules.tiny_api.requests.get')
def test_obter_produto_detalhado_success(mock_get):
    """Test fetching detailed product info with mocked response"""
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        'retorno': {
            'produto': {
                'codigo': 'DETAIL001',
                'nome': 'Produto Detalhado',
                'preco': '199,99',  # Tiny API retorna com vírgula
                'preco_custo': '100,00'
            }
        }
    }
    mock_get.return_value = mock_response
    
    with patch.object(config, 'TINY_API_TOKEN', 'test_token'):
        result = obter_produto_detalhado('DETAIL001')
        
        assert 'error' not in result
        assert result['codigo'] == 'DETAIL001'
        assert result['preco'] == 199.99

@patch('modules.tiny_api.requests.get')
def test_obter_produto_detalhado_error(mock_get):
    """Test detailed product fetch handles errors"""
    mock_get.side_effect = Exception('Network error')
    
    with patch.object(config, 'TINY_API_TOKEN', 'test_token'):
        result = obter_produto_detalhado('ERROR001')
        
        assert 'error' in result
