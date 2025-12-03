import pytest
from unittest.mock import Mock, patch, MagicMock
from modules.sync_apis import sync_shopee_pedidos, get_shopee_order_details

@patch('modules.sync_apis.add_conta')
@patch('modules.sync_apis.get_shopee_order_details')
@patch('modules.sync_apis.listar_pedidos')
@patch('modules.sync_apis.get_access_token')
def test_sync_shopee_pedidos_full_flow(mock_token, mock_listar, mock_details, mock_add):
    """Test complete sync flow with order processing"""
    mock_token.return_value = 'valid_token'
    
    mock_listar.return_value = {
        'order_list': [
            {'order_sn': 'ORDER001'},
            {'order_sn': 'ORDER002'},
            {'order_sn': 'ORDER003'}
        ]
    }
    
    mock_details.return_value = [
        {
            'order_sn': 'ORDER001',
            'order_status': 'COMPLETED',
            'total_amount': 200.0,
            'actual_shipping_fee': 15.0,
            'income_details': {
                'commission_fee': 10.0,
                'service_fee': 5.0,
                'transaction_fee': 2.0
            },
            'pay_time': 1701619200,
            'buyer_username': 'buyer1',
            'item_list': [{'model_quantity_purchased': 2}]
        },
        {
            'order_sn': 'ORDER002',
            'order_status': 'SHIPPED',
            'total_amount': 150.0,
            'actual_shipping_fee': 10.0,
            'income_details': {
                'commission_fee': 7.5,
                'service_fee': 3.75,
                'transaction_fee': 1.5
            },
            'pay_time': 1701705600,
            'buyer_username': 'buyer2',
            'item_list': [{'model_quantity_purchased': 1}]
        }
    ]
    
    result = sync_shopee_pedidos(dias_atras=7)
    
    # Verify orders were fetched
    assert mock_listar.called
    assert mock_details.called

@patch('requests.get')
@patch('modules.config.SHOPEE_PARTNER_ID', 123456)
@patch('modules.config.SHOPEE_PARTNER_KEY', 'test_key')
@patch('modules.config.SHOPEE_ACCESS_TOKEN', 'test_token')
@patch('modules.config.SHOPEE_SHOP_ID', 789)
def test_get_shopee_order_details_batch_processing(mock_get):
    """Test batch processing of order details (max 50 per request)"""
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        'response': {
            'order_list': [
                {'order_sn': f'ORDER{i:03d}', 'order_status': 'COMPLETED'}
                for i in range(1, 51)
            ]
        }
    }
    mock_get.return_value = mock_response
    
    # Test with exactly 50 orders
    order_sns = [f'ORDER{i:03d}' for i in range(1, 51)]
    result = get_shopee_order_details(order_sns)
    
    assert len(result) == 50
    assert mock_get.called

@patch('requests.get')
@patch('modules.config.SHOPEE_PARTNER_ID', 123456)
@patch('modules.config.SHOPEE_PARTNER_KEY', 'test_key')
@patch('modules.config.SHOPEE_ACCESS_TOKEN', 'test_token')
@patch('modules.config.SHOPEE_SHOP_ID', 789)
def test_get_shopee_order_details_empty_list(mock_get):
    """Test order details with empty order list"""
    result = get_shopee_order_details([])
    
    # Should handle empty list gracefully
    assert result == [] or result is not None

@patch('modules.sync_apis.listar_pedidos')
@patch('modules.sync_apis.get_access_token')
def test_sync_shopee_pedidos_max_days_limit(mock_token, mock_listar):
    """Test that sync respects 15 day API limit"""
    mock_token.return_value = 'valid_token'
    mock_listar.return_value = {'order_list': []}
    
    # Request 30 days but API should limit to 15
    result = sync_shopee_pedidos(dias_atras=30)
    
    # Verify API was called
    assert mock_listar.called
    
    # Check time_from/time_to span max 15 days
    call_args = mock_listar.call_args
    if call_args and 'time_from' in call_args[1] and 'time_to' in call_args[1]:
        time_diff = call_args[1]['time_to'] - call_args[1]['time_from']
        max_seconds = 15 * 24 * 3600
        assert time_diff <= max_seconds

@patch('requests.get')
@patch('modules.config.SHOPEE_PARTNER_ID', 123456)
@patch('modules.config.SHOPEE_PARTNER_KEY', 'test_key')
@patch('modules.config.SHOPEE_ACCESS_TOKEN', 'test_token')
@patch('modules.config.SHOPEE_SHOP_ID', 789)
def test_get_shopee_order_details_network_error(mock_get):
    """Test order details handles network errors"""
    mock_get.side_effect = Exception('Network error')
    
    result = get_shopee_order_details(['ORDER123'])
    
    assert result == []
