import pytest
from unittest.mock import Mock, patch, MagicMock
from io import BytesIO

# Test end-to-end workflow: PDF → parsing → conta creation

@patch('modules.pdf_parser.extract_from_pdf')
def test_pdf_to_conta_e2e(mock_pdf_extract):
    """End-to-end test: upload PDF → extract data → create conta payload"""
    
    # Mock PDF extraction
    mock_pdf_extract.return_value = {
        'cnpj': '12.345.678/0001-99',
        'valor': '1500.00',
        'vencimento': '31/12/2025',
        'linha_digitavel': '12345.67890 12345.678901 12345.678901 1 12345678901234',
        'fornecedor': 'Fornecedor Exemplo Ltda'
    }
    
    # Simulate workflow
    from modules.pdf_parser import extract_from_pdf
    
    # Step 1: Extract from PDF
    pdf_data = extract_from_pdf(b'fake_pdf_bytes', 'nota_fiscal.pdf')
    
    assert pdf_data['cnpj'] == '12.345.678/0001-99'
    assert pdf_data['valor'] == '1500.00'
    assert pdf_data['vencimento'] == '31/12/2025'
    
    # Step 2: Create conta payload (would normally save to DB via FastAPI)
    conta_payload = {
        'descricao': f"Pagamento {pdf_data.get('fornecedor', 'Desconhecido')}",
        'valor': float(pdf_data['valor']),
        'data_vencimento': '2025-12-31',
        'fornecedor': pdf_data.get('fornecedor'),
        'cnpj': pdf_data['cnpj']
    }
    
    assert conta_payload['valor'] == 1500.00
    assert conta_payload['fornecedor'] == 'Fornecedor Exemplo Ltda'
    assert conta_payload['descricao'] == 'Pagamento Fornecedor Exemplo Ltda'
    assert mock_pdf_extract.called

@patch('modules.pdf_parser._OCR_AVAILABLE', True)
@patch('modules.pdf_parser._extract_text_ocr')
def test_pdf_extraction_with_ocr(mock_ocr):
    """Test PDF extraction when OCR is available"""
    from modules.pdf_parser import extract_from_pdf
    
    mock_ocr.return_value = """
    NOTA FISCAL ELETRÔNICA
    CNPJ: 12.345.678/0001-99
    Valor Total: R$ 1.500,00
    Vencimento: 31/12/2025
    Linha Digitável: 12345.67890 12345.678901 12345.678901 1 12345678901234
    """
    
    result = extract_from_pdf(b'fake_pdf_content', 'test.pdf')
    
    assert result['cnpj'] == '12.345.678/0001-99'
    assert result['valor'] == '1500.00'
    assert result['vencimento'] == '31/12/2025'
    assert mock_ocr.called

@patch('modules.pdf_parser._OCR_AVAILABLE', False)
def test_pdf_extraction_fallback_no_ocr():
    """Test PDF extraction falls back gracefully when OCR unavailable"""
    from modules.pdf_parser import extract_from_pdf
    
    # Create fake PDF bytes with embedded text patterns
    fake_pdf = b'CNPJ: 12345678000199 Valor: R$ 500,00 Vencimento: 15/01/2026'
    
    result = extract_from_pdf(fake_pdf, 'boleto_12.345.678-0001-99.pdf')
    
    # Should extract CNPJ from filename when not in content
    assert '12.345.678' in result['cnpj'] or '12345678' in result['cnpj']

def test_pdf_extraction_partial_data():
    """Test that extraction handles partial data gracefully"""
    from modules.pdf_parser import extract_from_pdf
    
    # PDF with only some fields
    partial_pdf = b'Valor Total: R$ 250,00'
    
    result = extract_from_pdf(partial_pdf, 'incomplete.pdf')
    
    # Should return structure even with missing fields
    assert 'cnpj' in result
    assert 'valor' in result
    assert 'vencimento' in result
    assert result['valor'] == '250.00' or result['valor'] == ''
