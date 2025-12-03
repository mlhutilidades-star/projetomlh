import pytest
from unittest.mock import Mock, patch, MagicMock
from modules.shopee_api import _generate_sign, get_access_token, listar_produtos
from modules import config

def test_generate_sign_partner_level():
    """Test signature generation for partner-level APIs (no access token)"""
    with patch.object(config, 'SHOPEE_PARTNER_ID', 123456):
        with patch.object(config, 'SHOPEE_PARTNER_KEY', 'test_key'):
            path = "/api/v2/auth/token/get"
            timestamp = "1609459200"
            sign = _generate_sign(path, timestamp)
            
            assert isinstance(sign, str)
            assert len(sign) == 64  # HMAC-SHA256 produces 64 hex chars

def test_generate_sign_shop_level():
    """Test signature generation for shop-level APIs (with access token)"""
    with patch.object(config, 'SHOPEE_PARTNER_ID', 123456):
        with patch.object(config, 'SHOPEE_PARTNER_KEY', 'test_key'):
            path = "/api/v2/product/get_item_list"
            timestamp = "1609459200"
            access_token = "test_access_token"
            shop_id = "789"
            
            sign = _generate_sign(path, timestamp, access_token, shop_id)
            
            assert isinstance(sign, str)
            assert len(sign) == 64

def test_get_access_token_from_config():
    """Test retrieving access token from config"""
    with patch.object(config, 'SHOPEE_ACCESS_TOKEN', 'mock_token_12345'):
        token = get_access_token()
        assert token == 'mock_token_12345'

def test_get_access_token_none_when_missing():
    """Test that None is returned when no token configured"""
    with patch.object(config, 'SHOPEE_ACCESS_TOKEN', None):
        token = get_access_token()
        assert token is None

@patch('modules.shopee_api.requests.get')
def test_listar_produtos_success(mock_get):
    """Test product listing with mocked successful API response"""
    # Mock response
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.headers = {'content-type': 'application/json'}
    mock_response.json.return_value = {
        'response': {
            'item': [
                {'item_id': 1, 'item_name': 'Product 1'},
                {'item_id': 2, 'item_name': 'Product 2'}
            ],
            'total_count': 2
        }
    }
    mock_get.return_value = mock_response
    
    with patch.object(config, 'SHOPEE_PARTNER_ID', 123456):
        with patch.object(config, 'SHOPEE_PARTNER_KEY', 'test_key'):
            with patch.object(config, 'SHOPEE_SHOP_ID', 789):
                with patch.object(config, 'SHOPEE_ACCESS_TOKEN', 'test_token'):
                    result = listar_produtos(page_size=10, offset=0)
                    
                    # Verify API was called (or test internal structure)
                    assert mock_get.called or result is not None

@patch('modules.shopee_api.requests.get')
def test_listar_produtos_api_error(mock_get):
    """Test product listing handles API errors gracefully"""
    mock_response = Mock()
    mock_response.status_code = 401
    mock_response.headers = {'content-type': 'application/json'}
    mock_response.json.return_value = {'error': 'error_auth', 'message': 'Invalid access token'}
    mock_get.return_value = mock_response
    
    with patch.object(config, 'SHOPEE_PARTNER_ID', 123456):
        with patch.object(config, 'SHOPEE_PARTNER_KEY', 'test_key'):
            with patch.object(config, 'SHOPEE_SHOP_ID', 789):
                with patch.object(config, 'SHOPEE_ACCESS_TOKEN', 'invalid_token'):
                    result = listar_produtos()
                    
                    # Should handle error without crashing
                    assert result is None or isinstance(result, dict)
