# tests/unit/test_shopee_integration.py
import unittest
from unittest.mock import patch, MagicMock
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from integrations.shopee.auth import ShopeeAuth
from integrations.shopee.orders import ShopeeOrders
from integrations.shopee.products import ShopeeProducts


class TestShopeeIntegration(unittest.TestCase):
    @patch.dict(os.environ, {
        'SHOPEE_PARTNER_ID': '123456',
        'SHOPEE_PARTNER_KEY': 'test_key',
        'SHOPEE_SHOP_ID': '789012'
    })
    def test_auth_initialization(self):
        auth = ShopeeAuth()
        self.assertEqual(auth.partner_id, 123456)
        self.assertEqual(auth.shop_id, 789012)

    @patch.dict(os.environ, {
        'SHOPEE_PARTNER_ID': '123456',
        'SHOPEE_PARTNER_KEY': 'test_key',
        'SHOPEE_SHOP_ID': '789012'
    })
    @patch('integrations.shopee.orders.requests.get')
    def test_get_order_list_success(self, mock_get):
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "error": 0,
            "response": [
                {"order_sn": "123456789", "total_amount": 100.00},
                {"order_sn": "987654321", "total_amount": 150.00}
            ]
        }
        mock_get.return_value = mock_response

        auth = ShopeeAuth()
        orders_manager = ShopeeOrders(auth)
        orders = orders_manager.get_order_list()

        self.assertEqual(len(orders), 2)
        self.assertEqual(orders[0]["order_sn"], "123456789")

    @patch.dict(os.environ, {
        'SHOPEE_PARTNER_ID': '123456',
        'SHOPEE_PARTNER_KEY': 'test_key',
        'SHOPEE_SHOP_ID': '789012'
    })
    @patch('integrations.shopee.orders.requests.get')
    def test_get_order_list_error(self, mock_get):
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "error": 1,
            "message": "Unauthorized"
        }
        mock_get.return_value = mock_response

        auth = ShopeeAuth()
        orders_manager = ShopeeOrders(auth)
        orders = orders_manager.get_order_list()

        self.assertEqual(len(orders), 0)

    @patch.dict(os.environ, {
        'SHOPEE_PARTNER_ID': '123456',
        'SHOPEE_PARTNER_KEY': 'test_key',
        'SHOPEE_SHOP_ID': '789012'
    })
    @patch('integrations.shopee.orders.requests.get')
    def test_get_order_list_connection_error(self, mock_get):
        mock_get.side_effect = ConnectionError("Network error")

        auth = ShopeeAuth()
        orders_manager = ShopeeOrders(auth)
        orders = orders_manager.get_order_list()

        self.assertEqual(len(orders), 0)


class TestShopeeProducts(unittest.TestCase):
    @patch.dict(os.environ, {
        'SHOPEE_PARTNER_ID': '123456',
        'SHOPEE_PARTNER_KEY': 'test_key',
        'SHOPEE_SHOP_ID': '789012'
    })
    @patch('integrations.shopee.products.requests.get')
    def test_get_products_list_success(self, mock_get):
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "error": 0,
            "response": {
                "item": [
                    {"item_id": 1001, "item_name": "Produto 1", "price": "99.99"},
                    {"item_id": 1002, "item_name": "Produto 2", "price": "149.99"}
                ]
            }
        }
        mock_get.return_value = mock_response

        auth = ShopeeAuth()
        products_manager = ShopeeProducts(auth)
        products = products_manager.get_products_list()

        self.assertEqual(len(products), 2)
        self.assertEqual(products[0]["item_id"], 1001)

    @patch.dict(os.environ, {
        'SHOPEE_PARTNER_ID': '123456',
        'SHOPEE_PARTNER_KEY': 'test_key',
        'SHOPEE_SHOP_ID': '789012'
    })
    @patch('integrations.shopee.products.requests.get')
    def test_get_product_details_success(self, mock_get):
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "error": 0,
            "response": {
                "item_id": 1001,
                "item_name": "Produto 1",
                "price": "99.99",
                "stock": 50
            }
        }
        mock_get.return_value = mock_response

        auth = ShopeeAuth()
        products_manager = ShopeeProducts(auth)
        product = products_manager.get_product_details(1001)

        self.assertEqual(product["item_id"], 1001)
        self.assertEqual(product["stock"], 50)

    @patch.dict(os.environ, {
        'SHOPEE_PARTNER_ID': '123456',
        'SHOPEE_PARTNER_KEY': 'test_key',
        'SHOPEE_SHOP_ID': '789012'
    })
    @patch('integrations.shopee.products.requests.get')
    def test_get_product_details_error(self, mock_get):
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "error": 1,
            "message": "Item not found"
        }
        mock_get.return_value = mock_response

        auth = ShopeeAuth()
        products_manager = ShopeeProducts(auth)
        product = products_manager.get_product_details(9999)

        self.assertEqual(len(product), 0)


if __name__ == '__main__':
    unittest.main()
