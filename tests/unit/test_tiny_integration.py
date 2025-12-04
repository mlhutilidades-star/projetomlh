# tests/unit/test_tiny_integration.py
import unittest
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from integrations.tiny_erp.auth import TinyERPAuth
from integrations.tiny_erp.invoices import TinyERPInvoiceFetcher
from integrations.tiny_erp.payables import TinyERPPayables

class TestTinyERPIntegration(unittest.TestCase):
    @patch.dict(os.environ, {'TINY_API_TOKEN': 'fake_token'})
    def test_auth_get_token_success(self):
        auth = TinyERPAuth()
        auth._token_expiry_time = datetime.now() - timedelta(seconds=1)
        with patch.object(auth, '_request_new_token') as mock_request:
            auth.get_access_token()
            mock_request.assert_called_once()

    @patch('integrations.tiny_erp.invoices.requests.get')
    def test_search_invoices_success(self, mock_get):
        mock_response = MagicMock()
        mock_response.json.return_value = {"retorno": {"status": "OK", "notas_fiscais": [{"id": 1}]}}
        mock_get.return_value = mock_response
        mock_auth = MagicMock(spec=TinyERPAuth)
        mock_auth.get_access_token.return_value = "fake_token"
        fetcher = TinyERPInvoiceFetcher(mock_auth)
        invoices = fetcher.search_purchase_invoices("01/01/2024", "31/01/2024")
        self.assertEqual(len(invoices), 1)

    @patch('integrations.tiny_erp.payables.requests.post')
    def test_create_payable_success(self, mock_post):
        mock_response = MagicMock()
        mock_response.json.return_value = {"retorno": {"status": "OK"}}
        mock_post.return_value = mock_response
        mock_auth = MagicMock(spec=TinyERPAuth)
        mock_auth.get_access_token.return_value = "fake_token"
        payables_manager = TinyERPPayables(mock_auth)
        result = payables_manager.create_payable({"valor": "100"})
        self.assertEqual(result['status'], "OK")
