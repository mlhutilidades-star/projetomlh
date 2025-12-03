import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta

def test_sync_apis_imports():
    """Test that sync_apis module imports correctly"""
    import importlib
    mod = importlib.import_module('modules.sync_apis')
    assert hasattr(mod, 'sync_shopee_pedidos') or hasattr(mod, 'get_shopee_order_details') or mod is not None

@patch('requests.get')
@patch('modules.config.SHOPEE_PARTNER_ID', 123456)
@patch('modules.config.SHOPEE_PARTNER_KEY', 'test_key')
@patch('modules.config.SHOPEE_ACCESS_TOKEN', 'test_token')
@patch('modules.config.SHOPEE_SHOP_ID', 789)
def test_get_shopee_order_details_success(mock_get):
    """Test fetching Shopee order details with mocked API response"""
    from modules.sync_apis import get_shopee_order_details
    
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        'response': {
            'order_list': [
                {
                    'order_sn': 'ORDER123',
                    'order_status': 'COMPLETED',
                    'total_amount': 150.00,
                    'actual_shipping_fee': 10.00
                }
            ]
        }
    }
    mock_get.return_value = mock_response
    
    result = get_shopee_order_details(['ORDER123'])
    
    assert len(result) == 1
    assert result[0]['order_sn'] == 'ORDER123'
    assert mock_get.called

@patch('requests.get')
@patch('modules.config.SHOPEE_PARTNER_ID', 123456)
@patch('modules.config.SHOPEE_PARTNER_KEY', 'test_key')
@patch('modules.config.SHOPEE_ACCESS_TOKEN', 'test_token')
@patch('modules.config.SHOPEE_SHOP_ID', 789)
def test_get_shopee_order_details_error(mock_get):
    """Test handling API errors when fetching order details"""
    from modules.sync_apis import get_shopee_order_details
    
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        'error': 'error_auth',
        'message': 'Invalid access token'
    }
    mock_get.return_value = mock_response
    
    result = get_shopee_order_details(['ORDER123'])
    
    assert result == []

@patch('modules.config.SHOPEE_ACCESS_TOKEN', None)
def test_get_shopee_order_details_no_token():
    """Test that missing access token returns empty list"""
    from modules.sync_apis import get_shopee_order_details
    
    result = get_shopee_order_details(['ORDER123'])
    
    assert result == []

@patch('modules.sync_apis.get_access_token')
def test_sync_shopee_pedidos_no_token(mock_get_token):
    """Test sync aborts when no access token available"""
    from modules.sync_apis import sync_shopee_pedidos
    
    mock_get_token.return_value = None
    
    result = sync_shopee_pedidos(dias_atras=7)
    
    assert result['total_importados'] == 0
    assert result['total_erros'] == 1
    assert 'erro' in result

@patch('modules.sync_apis.get_shopee_order_details')
@patch('modules.sync_apis.listar_pedidos')
@patch('modules.sync_apis.get_access_token')
def test_sync_shopee_pedidos_no_orders(mock_get_token, mock_listar, mock_get_details):
    """Test sync when no orders in period"""
    from modules.sync_apis import sync_shopee_pedidos
    
    mock_get_token.return_value = 'test_token'
    mock_listar.return_value = {'order_list': []}
    
    result = sync_shopee_pedidos(dias_atras=7)
    
    assert result['total_importados'] == 0
    assert result['total_erros'] == 0
    assert 'mensagem' in result
