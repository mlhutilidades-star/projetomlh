# tests/unit/test_pdf_processor.py
import unittest
from unittest.mock import patch, MagicMock, mock_open
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from modules.pdf_processor import PDFBoletoProcessor


class TestPDFBoletoProcessor(unittest.TestCase):
    def setUp(self):
        self.processor = PDFBoletoProcessor()

    @patch('modules.pdf_processor.pdfplumber.open')
    def test_extract_text_from_pdf_success(self, mock_pdf_open):
        # Mock do PDF
        mock_page = MagicMock()
        mock_page.extract_text.return_value = "Valor: R$ 100.00\nVencimento: 15/12/2024"
        
        mock_pdf = MagicMock()
        mock_pdf.pages = [mock_page]
        mock_pdf.__enter__ = MagicMock(return_value=mock_pdf)
        mock_pdf.__exit__ = MagicMock(return_value=None)
        
        mock_pdf_open.return_value = mock_pdf
        
        text = self.processor.extract_text_from_pdf("boleto.pdf")
        
        self.assertIn("Valor: R$ 100.00", text)
        self.assertIn("Vencimento: 15/12/2024", text)

    @patch('modules.pdf_processor.pdfplumber.open')
    def test_extract_text_from_pdf_not_found(self, mock_pdf_open):
        mock_pdf_open.side_effect = FileNotFoundError("Arquivo não encontrado")
        
        text = self.processor.extract_text_from_pdf("inexistente.pdf")
        
        self.assertEqual(text, "")

    @patch('modules.pdf_processor.pdfplumber.open')
    def test_extract_boleto_data(self, mock_pdf_open):
        # Mock do PDF
        mock_page = MagicMock()
        mock_page.extract_text.return_value = """
        Banco: 123
        Agência: 4567
        Conta: 89012345
        Valor: R$ 500.00
        Vencimento: 20/12/2024
        Cedente: Empresa LTDA
        Sacado: Cliente Ltda
        """
        
        mock_pdf = MagicMock()
        mock_pdf.pages = [mock_page]
        mock_pdf.__enter__ = MagicMock(return_value=mock_pdf)
        mock_pdf.__exit__ = MagicMock(return_value=None)
        
        mock_pdf_open.return_value = mock_pdf
        
        result = self.processor.extract_boleto_data("boleto.pdf")
        
        self.assertEqual(result["status"], "processado")
        self.assertIn("banco", result["dados_extraidos"])
        self.assertIn("agencia", result["dados_extraidos"])
        self.assertIn("valor", result["dados_extraidos"])

    def test_extract_value_from_text_success(self):
        text = "O valor total é R$ 1.250,00 para este boleto"
        value = self.processor.extract_value_from_text(text)
        
        self.assertAlmostEqual(value, 1250.00, places=2)

    def test_extract_value_from_text_with_dot(self):
        text = "Valor cobrado: R$ 999.99"
        value = self.processor.extract_value_from_text(text)
        
        self.assertAlmostEqual(value, 999.99, places=2)

    def test_extract_value_from_text_not_found(self):
        text = "Este texto não contém valor monetário"
        value = self.processor.extract_value_from_text(text)
        
        self.assertIsNone(value)

    @patch.object(PDFBoletoProcessor, 'extract_boleto_data')
    def test_process_multiple_boletos(self, mock_extract):
        # Mock do resultado de extração
        mock_extract.return_value = {
            "status": "processado",
            "dados_extraidos": {"valor": "R$ 100.00"}
        }
        
        pdf_list = ["boleto1.pdf", "boleto2.pdf", "boleto3.pdf"]
        results = self.processor.process_multiple_boletos(pdf_list)
        
        self.assertEqual(len(results), 3)
        self.assertEqual(mock_extract.call_count, 3)
        self.assertEqual(results[0]["status"], "processado")


if __name__ == '__main__':
    unittest.main()
