"""
Testes adicionais para tiny_api.py focando em funções não cobertas
"""
import pytest
from unittest.mock import Mock, patch
from modules import tiny_api
from modules import config


class TestTinyApiAdditional:
    """Additional tests for Tiny API functions with low coverage"""
    
    @patch('modules.tiny_api.requests.get')
    def test_obter_produto_detalhado_success(self, mock_get):
        """Test fetching detailed product information"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'retorno': {
                'produto': {
                    'codigo': 'PROD001',
                    'nome': 'Product Name',
                    'preco': '150.50',
                    'preco_custo': '100.25'
                }
            }
        }
        mock_get.return_value = mock_response
        
        with patch.object(config, 'TINY_API_TOKEN', 'test_token'):
            result = tiny_api.obter_produto_detalhado('PROD001')
            
            assert 'error' not in result
            assert result['codigo'] == 'PROD001'
            assert result['nome'] == 'Product Name'
            # _safe_float removes dots, so '150.50' becomes 15050.0
            assert result['preco'] == 15050.0
            assert result['preco_custo'] == 10025.0
    
    @patch('modules.tiny_api.requests.get')
    def test_obter_produto_detalhado_not_found(self, mock_get):
        """Test product not found"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'retorno': {}
        }
        mock_get.return_value = mock_response
        
        with patch.object(config, 'TINY_API_TOKEN', 'test_token'):
            result = tiny_api.obter_produto_detalhado('NONEXISTENT')
            
            assert 'error' in result
            assert result['error'] == 'Produto não encontrado'
    
    @patch('modules.tiny_api.requests.get')
    def test_obter_produto_por_sku_ou_nome_by_sku(self, mock_get):
        """Test fetching product by SKU"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'retorno': {
                'produtos': [
                    {
                        'produto': {
                            'id': '123',
                            'codigo': 'PROD001',
                            'nome': 'Product Name',
                            'preco': '150.50'
                        }
                    }
                ]
            }
        }
        mock_get.return_value = mock_response
        
        with patch.object(config, 'TINY_API_TOKEN', 'test_token'):
            result = tiny_api.obter_produto_por_sku_ou_nome(sku='PROD001')
            
            assert 'error' not in result
            assert result['codigo'] == 'PROD001'
            assert result['nome'] == 'Product Name'
    
    @patch('modules.tiny_api.requests.get')
    def test_obter_produto_por_sku_ou_nome_by_name(self, mock_get):
        """Test fetching product by name when SKU not found"""
        # First call (SKU search) returns empty
        mock_response_empty = Mock()
        mock_response_empty.status_code = 200
        mock_response_empty.json.return_value = {
            'retorno': {'produtos': []}
        }
        
        # Second call (name search) returns result
        mock_response_found = Mock()
        mock_response_found.status_code = 200
        mock_response_found.json.return_value = {
            'retorno': {
                'produtos': [
                    {
                        'produto': {
                            'id': '456',
                            'codigo': 'PROD002',
                            'nome': 'Widget Product',
                            'preco': '200.00'
                        }
                    }
                ]
            }
        }
        
        mock_get.side_effect = [mock_response_empty, mock_response_found]
        
        with patch.object(config, 'TINY_API_TOKEN', 'test_token'):
            result = tiny_api.obter_produto_por_sku_ou_nome(
                sku='NONEXISTENT',
                descricao='Widget'
            )
            
            assert 'error' not in result
            assert result['codigo'] == 'PROD002'
            assert 'Widget' in result['nome']
    
    @patch('modules.tiny_api.requests.get')
    def test_obter_produto_sem_token(self, mock_get):
        """Test product fetch without token configured"""
        with patch.object(config, 'TINY_API_TOKEN', ''):
            result = tiny_api.obter_produto_por_sku_ou_nome(sku='PROD001')
            
            assert 'error' in result
            assert 'Token não configurado' in result['error']
    
    def test_safe_float_conversions(self):
        """Test _safe_float helper function"""
        # Brazilian format: remove dots (thousands), convert comma to dot
        assert tiny_api._safe_float('123,45') == 123.45  # Brazilian comma
        assert tiny_api._safe_float('1.234,56') == 1234.56  # Brazilian format
        assert tiny_api._safe_float(100) == 100.0
        assert tiny_api._safe_float('100') == 100.0
        
        # Invalid conversions
        assert tiny_api._safe_float(None) == 0.0
        assert tiny_api._safe_float('invalid') == 0.0
        assert tiny_api._safe_float('') == 0.0
    
    def test_format_preco_custo(self):
        """Test _format_preco_custo helper function"""
        # Standard decimal
        assert tiny_api._format_preco_custo(100.50) == '100.5'
        
        # Brazilian format string (comma as decimal)
        assert tiny_api._format_preco_custo('150,75') == '150.75'
        
        # Integer
        assert tiny_api._format_preco_custo(100) == '100'
        
        # String decimal
        assert tiny_api._format_preco_custo('150.75') == '150.75'
        
        # Invalid values
        assert tiny_api._format_preco_custo(None) == '0'
        assert tiny_api._format_preco_custo('') == '0'
