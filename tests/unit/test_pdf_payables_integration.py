# tests/unit/test_pdf_payables_integration.py
import unittest
from unittest.mock import patch, MagicMock
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from modules.pdf_payables_integration import PDFPayablesIntegration


class TestPDFPayablesIntegration(unittest.TestCase):
    def setUp(self):
        # Mock do TinyERPAuth para evitar carregamento de variáveis de ambiente
        self.mock_auth = MagicMock()
        self.integrador = PDFPayablesIntegration(tiny_auth=self.mock_auth)

    @patch('modules.pdf_payables_integration.PDFBoletoProcessor')
    def test_extract_and_prefill_success(self, mock_processor_class):
        # Mock do processador de PDF
        mock_processor = MagicMock()
        mock_processor_class.return_value = mock_processor
        
        mock_processor.extract_boleto_data.return_value = {
            "status": "processado",
            "dados_extraidos": {
                "valor": "R$ 100.00",
                "vencimento": "15/12/2024",
                "cedente": "Empresa X",
                "banco": "001"
            }
        }
        
        # Recria integrador com processor mockado
        integrador = PDFPayablesIntegration(tiny_auth=self.mock_auth)
        integrador.pdf_processor = mock_processor
        
        # Mock do gerenciador de contas a pagar
        with patch.object(integrador.payables_manager, 'create_payable') as mock_create:
            mock_create.return_value = {"status": "OK"}
            
            result = integrador.extract_and_prefill("boleto.pdf")
        
        self.assertEqual(result["status"], "sucesso")
        self.assertEqual(result["arquivo"], "boleto.pdf")
        self.assertIn("dados_extraidos", result)

    def test_extract_and_prefill_no_data(self):
        # Mock do processador
        with patch.object(self.integrador.pdf_processor, 'extract_boleto_data') as mock_extract:
            mock_extract.return_value = {
                "status": "processado",
                "dados_extraidos": {}
            }
            
            result = self.integrador.extract_and_prefill("boleto_vazio.pdf")
        
        self.assertEqual(result["status"], "erro")
        self.assertIn("Não foi possível extrair dados", result["mensagem"])

    def test_parse_valor(self):
        valor = self.integrador._parse_valor("R$ 250,50")
        self.assertAlmostEqual(valor, 250.50, places=2)

    def test_parse_data_vencimento_slash(self):
        data = self.integrador._parse_data_vencimento("Data: 15/12/2024")
        self.assertEqual(data, "15/12/2024")

    def test_parse_data_vencimento_dash(self):
        data = self.integrador._parse_data_vencimento("Vencimento: 05-01-2025")
        self.assertEqual(data, "05/01/2025")

    def test_extract_numero_boleto(self):
        extracted = {
            "cedente": "Empresa X",
            "conta": "123456",
            "nosso_numero": "9876543"
        }
        
        numero = self.integrador._extract_numero_boleto(extracted)
        # Deve retornar nosso_numero se disponível
        self.assertNotEqual(numero, "")

    @patch.object(PDFPayablesIntegration, 'extract_and_prefill')
    def test_extract_and_prefill_batch(self, mock_extract):
        # Mock retornando sucesso para 2 e erro para 1
        mock_extract.side_effect = [
            {"status": "sucesso", "arquivo": "boleto1.pdf"},
            {"status": "sucesso", "arquivo": "boleto2.pdf"},
            {"status": "erro", "arquivo": "boleto3.pdf", "mensagem": "Erro"}
        ]
        
        pdf_list = ["boleto1.pdf", "boleto2.pdf", "boleto3.pdf"]
        results = self.integrador.extract_and_prefill_batch(pdf_list)
        
        self.assertEqual(len(results), 3)
        self.assertEqual(mock_extract.call_count, 3)
        
        # Verifica sucessos e erros
        success_count = sum(1 for r in results if r.get("status") == "sucesso")
        self.assertEqual(success_count, 2)

    def test_map_boleto_to_payable(self):
        boleto_data = {
            "dados_extraidos": {
                "valor": "R$ 500.00",
                "vencimento": "20/12/2024",
                "cedente": "Fornecedor ABC",
                "banco": "123",
                "agencia": "4567",
                "conta": "89012345"
            }
        }
        
        payable = self.integrador._map_boleto_to_payable(boleto_data)
        
        self.assertIn("descricao", payable)
        self.assertIn("valor", payable)
        self.assertIn("data_vencimento", payable)
        self.assertEqual(payable["fornecedor_nome"], "Fornecedor ABC")


if __name__ == '__main__':
    unittest.main()
