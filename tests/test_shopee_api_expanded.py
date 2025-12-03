import pytest
from unittest.mock import Mock, patch
from modules.shopee_api import (
    _generate_sign,
    get_access_token,
    listar_produtos,
    _refresh_access_token,
    _update_env_tokens
)
from modules import config

@patch('modules.config.SHOPEE_PARTNER_ID', 123456)
@patch('modules.config.SHOPEE_PARTNER_KEY', 'test_partner_key')
def test_generate_sign_consistency():
    """Test that sign generation is deterministic"""
    path = "/api/v2/product/get_item_list"
    timestamp = "1609459200"
    access_token = "test_token"
    shop_id = "789"
    
    sign1 = _generate_sign(path, timestamp, access_token, shop_id)
    sign2 = _generate_sign(path, timestamp, access_token, shop_id)
    
    assert sign1 == sign2
    assert len(sign1) == 64

@patch('modules.shopee_api.requests.get')
@patch('modules.config.SHOPEE_PARTNER_ID', 123456)
@patch('modules.config.SHOPEE_PARTNER_KEY', 'test_key')
@patch('modules.config.SHOPEE_ACCESS_TOKEN', 'test_token')
@patch('modules.config.SHOPEE_SHOP_ID', 789)
def test_listar_produtos_pagination(mock_get):
    """Test product listing with pagination"""
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.headers = {'content-type': 'application/json'}
    mock_response.json.return_value = {
        'response': {
            'item': [
                {'item_id': i, 'item_name': f'Product {i}'}
                for i in range(1, 21)
            ],
            'total_count': 50,
            'has_next_page': True
        }
    }
    mock_get.return_value = mock_response
    
    result = listar_produtos(page_size=20, offset=0)
    
    assert mock_get.called

@patch('modules.shopee_api.requests.post')
@patch('modules.config.SHOPEE_PARTNER_ID', 123456)
@patch('modules.config.SHOPEE_PARTNER_KEY', 'test_key')
@patch('modules.config.SHOPEE_SHOP_ID', 789)
@patch('os.getenv')
def test_refresh_access_token_success(mock_getenv, mock_post):
    """Test successful token refresh"""
    mock_getenv.return_value = 'old_refresh_token'
    
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.headers = {'content-type': 'application/json'}
    mock_response.json.return_value = {
        'access_token': 'new_access_token',
        'refresh_token': 'new_refresh_token',
        'expires_in': 14400
    }
    mock_post.return_value = mock_response
    
    with patch('modules.shopee_api._update_env_tokens') as mock_update:
        result = _refresh_access_token()
        
        assert result == 'new_access_token'
        mock_update.assert_called_once_with('new_access_token', 'new_refresh_token')

@patch('modules.shopee_api.requests.post')
@patch('modules.config.SHOPEE_PARTNER_ID', 123456)
@patch('modules.config.SHOPEE_PARTNER_KEY', 'test_key')
@patch('modules.config.SHOPEE_SHOP_ID', 789)
@patch('os.getenv')
def test_refresh_access_token_failure(mock_getenv, mock_post):
    """Test token refresh handles API errors"""
    mock_getenv.return_value = 'old_refresh_token'
    
    mock_response = Mock()
    mock_response.status_code = 401
    mock_response.headers = {'content-type': 'application/json'}
    mock_response.json.return_value = {
        'error': 'error_auth',
        'message': 'Invalid refresh token'
    }
    mock_post.return_value = mock_response
    
    result = _refresh_access_token()
    
    assert result is None

@patch('builtins.open', create=True)
@patch('os.path.exists')
def test_update_env_tokens_creates_file(mock_exists, mock_open):
    """Test that env token update creates file if not exists"""
    mock_exists.return_value = False
    mock_file = Mock()
    mock_open.return_value.__enter__.return_value = mock_file
    
    with patch('os.environ', {}):
        result = _update_env_tokens('new_access', 'new_refresh')
        
        assert mock_open.called
        assert mock_file.writelines.called

@patch('modules.shopee_api.requests.get')
@patch('modules.config.SHOPEE_PARTNER_ID', 123456)
@patch('modules.config.SHOPEE_PARTNER_KEY', 'test_key')
@patch('modules.config.SHOPEE_ACCESS_TOKEN', None)
@patch('modules.config.SHOPEE_SHOP_ID', 789)
def test_listar_produtos_no_token(mock_get):
    """Test product listing without access token"""
    result = listar_produtos(page_size=10, offset=0)
    
    # Should return empty or error response
    assert result is None or 'error' in result or result == {}
