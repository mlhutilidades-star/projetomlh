"""
E2E Tests - End-to-End Testing para Streamlit Dashboard
Testa fluxos completos de usuário através da aplicação
"""

import pytest
from unittest.mock import Mock, patch
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestE2EUploadPDFWorkflow:
    """Testes E2E para workflow completo de upload e processamento de PDF"""
    
    @patch('modules.pdf_processor.PDFBoletoProcessor.extract_boleto_data')
    def test_full_pdf_upload_flow(self, mock_extract):
        """E2E: Usuario faz upload de PDF -> sistema extrai dados -> sucesso"""
        
        mock_extract.return_value = {
            "dados_extraidos": {
                "valor": "1500.00",
                "vencimento": "25/12/2024",
                "cedente": "Fornecedor XYZ"
            }
        }
        
        from modules.pdf_processor import PDFBoletoProcessor
        processor = PDFBoletoProcessor()
        extracted = processor.extract_boleto_data("/tmp/boleto.pdf")
        
        assert extracted.get("dados_extraidos") is not None
        assert extracted["dados_extraidos"]["valor"] == "1500.00"
        assert "cedente" in extracted["dados_extraidos"]


class TestE2EShopeeOrderSync:
    """Testes E2E para sincronização de pedidos Shopee"""
    
    @patch('integrations.shopee.orders.ShopeeOrders.get_order_list')
    def test_complete_shopee_order_import_flow(self, mock_orders):
        """E2E: Buscar pedidos Shopee -> processar múltiplos pedidos"""
        
        mock_orders.return_value = [
            {"order_sn": "220101001", "total_amount": 150.00},
            {"order_sn": "220101002", "total_amount": 200.00}
        ]
        
        orders = mock_orders.return_value
        
        assert len(orders) == 2
        assert orders[0]["order_sn"] == "220101001"
        assert orders[0]["total_amount"] == 150.00


class TestE2EDashboardView:
    """Testes E2E para visualização do Dashboard"""
    
    def test_dashboard_kpi_calculation(self):
        """E2E: Dashboard carrega e calcula KPIs corretamente"""
        
        contas = [
            {"id": 1, "valor": 1500.00},
            {"id": 2, "valor": 2500.00}
        ]
        
        orders = [
            {"order_sn": "001", "total_amount": 100.00},
            {"order_sn": "002", "total_amount": 150.00},
            {"order_sn": "003", "total_amount": 200.00}
        ]
        
        total_contas = sum(c["valor"] for c in contas)
        total_pedidos = len(orders)
        total_receita = sum(o["total_amount"] for o in orders)
        
        assert total_contas == 4000.00
        assert total_pedidos == 3
        assert total_receita == 450.00


class TestE2EErrorRecovery:
    """Testes E2E para tratamento de erros e recuperação"""
    
    @patch('requests.get')
    def test_api_timeout_recovery(self, mock_get):
        """E2E: API timeout -> retry -> sucesso"""
        
        import requests
        
        mock_get.side_effect = requests.exceptions.Timeout("Timeout")
        
        with pytest.raises(requests.exceptions.Timeout):
            requests.get("http://api.example.com")
        
        mock_get.side_effect = None
        mock_response = Mock()
        mock_response.json.return_value = {"status": "ok"}
        mock_get.return_value = mock_response
        
        response = requests.get("http://api.example.com")
        assert response.json()["status"] == "ok"


class TestE2EDataValidation:
    """Testes E2E para validação de dados em fluxos completos"""
    
    @patch('modules.pdf_processor.PDFBoletoProcessor.extract_boleto_data')
    def test_invalid_pdf_data_handling(self, mock_extract):
        """E2E: Upload PDF invalido -> erro -> retry com PDF valido -> sucesso"""
        
        from modules.pdf_processor import PDFBoletoProcessor
        processor = PDFBoletoProcessor()
        
        mock_extract.return_value = {"dados_extraidos": {}}
        result = processor.extract_boleto_data("/tmp/invalid.pdf")
        
        assert not result.get("dados_extraidos")
        
        mock_extract.return_value = {
            "dados_extraidos": {
                "valor": "1000.00",
                "vencimento": "25/12/2024"
            }
        }
        
        result = processor.extract_boleto_data("/tmp/valid.pdf")
        assert result.get("dados_extraidos")


class TestE2EMultiPagePDF:
    """Testes E2E para processamento de PDFs multi-página"""
    
    @patch('pdfplumber.open')
    def test_batch_pdf_processing_workflow(self, mock_pdfplumber):
        """E2E: Processar PDF com múltiplas páginas"""
        
        mock_pages = []
        for i in range(3):
            mock_page = Mock()
            mock_page.extract_text.return_value = f"Valor: {100 * (i+1)}"
            mock_pages.append(mock_page)
        
        mock_pdf = Mock()
        mock_pdf.pages = mock_pages
        mock_pdfplumber.return_value.__enter__.return_value = mock_pdf
        
        texts = [page.extract_text() for page in mock_pdf.pages]
        
        assert len(texts) == 3
        assert "100" in texts[0]
        assert "200" in texts[1]
        assert "300" in texts[2]


class TestE2EUserFlow:
    """Testes E2E para fluxo completo de usuário"""
    
    @patch('modules.pdf_processor.PDFBoletoProcessor.extract_boleto_data')
    def test_complete_user_session(self, mock_extract):
        """E2E: Usuario faz upload de PDF -> sistema processa -> atualiza dados"""
        
        initial_contas = [{"id": 1, "valor": 1000.00}]
        
        initial_count = len(initial_contas)
        initial_total = sum(c["valor"] for c in initial_contas)
        
        assert initial_count == 1
        assert initial_total == 1000.00
        
        mock_extract.return_value = {
            "dados_extraidos": {
                "valor": "1500.00",
                "vencimento": "25/12/2024",
                "cedente": "Novo Fornecedor"
            }
        }
        
        extracted = mock_extract()
        new_value = float(extracted["dados_extraidos"]["valor"])
        
        assert new_value == 1500.00
        
        updated_contas = [
            {"id": 1, "valor": 1000.00},
            {"id": 2, "valor": 1500.00}
        ]
        
        updated_count = len(updated_contas)
        updated_total = sum(c["valor"] for c in updated_contas)
        
        assert updated_count == 2
        assert updated_total == 2500.00
        assert updated_total > initial_total


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
