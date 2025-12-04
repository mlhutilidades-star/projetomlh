# tests/unit/test_shopee_integration.py
import unittest
from unittest.mock import patch, MagicMock
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from integrations.shopee.auth import ShopeeAuth
from integrations.shopee.orders import ShopeeOrders
from integrations.shopee.products import ShopeeProducts
from integrations.shopee.fees import ShopeeFees


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


class TestShopeeFees(unittest.TestCase):
    def setUp(self):
        self.fees_calculator = ShopeeFees()

    def test_calculate_commission_general(self):
        result = self.fees_calculator.calculate_commission(100.0, category="general")
        
        self.assertEqual(result["order_amount"], 100.0)
        self.assertEqual(result["commission_rate"], 5.0)
        self.assertEqual(result["commission_value"], 5.0)

    def test_calculate_commission_electronics(self):
        result = self.fees_calculator.calculate_commission(100.0, category="electronics")
        
        self.assertEqual(result["order_amount"], 100.0)
        self.assertEqual(result["commission_rate"], 6.0)
        self.assertEqual(result["commission_value"], 6.0)

    def test_calculate_payment_processing_fee_card(self):
        result = self.fees_calculator.calculate_payment_processing_fee(100.0, payment_method="card")
        
        self.assertEqual(result["order_amount"], 100.0)
        self.assertEqual(result["processing_rate"], 2.0)
        self.assertEqual(result["processing_fee"], 2.0)

    def test_calculate_payment_processing_fee_wallet(self):
        result = self.fees_calculator.calculate_payment_processing_fee(100.0, payment_method="wallet")
        
        self.assertEqual(result["order_amount"], 100.0)
        self.assertEqual(result["processing_rate"], 1.5)
        self.assertAlmostEqual(result["processing_fee"], 1.5, places=2)

    def test_calculate_total_fees(self):
        result = self.fees_calculator.calculate_total_fees(100.0, category="general", payment_method="card")
        
        self.assertEqual(result["gross_amount"], 100.0)
        self.assertEqual(result["commission"]["commission_value"], 5.0)
        self.assertEqual(result["payment_processing"]["processing_fee"], 2.0)
        self.assertEqual(result["total_fees"], 7.0)
        self.assertEqual(result["net_amount"], 93.0)

    def test_calculate_total_fees_with_percentage(self):
        result = self.fees_calculator.calculate_total_fees(200.0, category="electronics", payment_method="wallet")
        
        self.assertEqual(result["gross_amount"], 200.0)
        # Commission: 200 * 6% = 12.0
        # Payment: 200 * 1.5% = 3.0
        # Total: 15.0, Net: 185.0
        self.assertAlmostEqual(result["total_fees"], 15.0, places=1)
        self.assertAlmostEqual(result["net_amount"], 185.0, places=1)


if __name__ == '__main__':
    unittest.main()

    def test_calculate_total_fees_with_percentage(self):
        result = self.fees_calculator.calculate_total_fees(200.0, category="electronics", payment_method="wallet")
        
        self.assertEqual(result["gross_amount"], 200.0)
        # Commission: 200 * 6% = 12.0
        # Payment: 200 * 1.5% = 3.0
        # Total: 15.0, Net: 185.0
        self.assertAlmostEqual(result["total_fees"], 15.0, places=1)
        self.assertAlmostEqual(result["net_amount"], 185.0, places=1)
