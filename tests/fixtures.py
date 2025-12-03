import pytest
from datetime import datetime

@pytest.fixture
def sample_cnpj():
    """Sample CNPJ for testing"""
    return "12.345.678/0001-99"

@pytest.fixture
def sample_cnpj_clean():
    """Sample CNPJ without formatting"""
    return "12345678000199"

@pytest.fixture
def sample_conta_data():
    """Sample conta a pagar data"""
    return {
        'descricao': 'Fornecedor Teste Ltda',
        'valor': 1500.00,
        'data_vencimento': '2025-12-31',
        'fornecedor': 'Fornecedor Teste',
        'cnpj': '12.345.678/0001-99'
    }

@pytest.fixture
def sample_pdf_data():
    """Sample PDF extraction result"""
    return {
        'cnpj': '12.345.678/0001-99',
        'valor': '1500.00',
        'vencimento': '31/12/2025',
        'linha_digitavel': '12345.67890 12345.678901 12345.678901 1 12345678901234',
        'fornecedor': 'Fornecedor Exemplo Ltda'
    }

@pytest.fixture
def mock_shopee_order():
    """Sample Shopee order response"""
    return {
        'order_sn': 'ORDER123456',
        'order_status': 'COMPLETED',
        'total_amount': 200.0,
        'actual_shipping_fee': 15.0,
        'income_details': {
            'commission_fee': 10.0,
            'service_fee': 5.0,
            'transaction_fee': 2.0
        },
        'pay_time': 1701619200,
        'buyer_username': 'buyer_test',
        'item_list': [
            {'model_quantity_purchased': 2, 'item_name': 'Product 1'},
            {'model_quantity_purchased': 1, 'item_name': 'Product 2'}
        ]
    }

@pytest.fixture
def mock_tiny_product():
    """Sample Tiny ERP product response"""
    return {
        'codigo': 'PROD001',
        'nome': 'Produto Teste',
        'preco': '99,90',
        'preco_custo': '50,00',
        'estoque': 10
    }

@pytest.fixture
def mock_nfe_data():
    """Sample NFe data structure"""
    return {
        'numero': '12345',
        'serie': '1',
        'chave': '12345678901234567890123456789012345678901234',
        'data_emissao': datetime(2025, 12, 3),
        'valor_total': 1500.00,
        'fornecedor': {
            'cnpj': '12.345.678/0001-99',
            'razao_social': 'Fornecedor Teste Ltda',
            'ie': '123456789'
        },
        'itens': [
            {
                'codigo': 'ITEM001',
                'descricao': 'Item Teste',
                'quantidade': 10,
                'valor_unitario': 150.00,
                'valor_total': 1500.00
            }
        ]
    }
