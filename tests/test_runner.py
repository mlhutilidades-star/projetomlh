"""
Automated test suite for Hub Financeiro
Run with: python -m pytest tests/ -v
Or direct: python tests/test_runner.py
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

# DATABASE_URL agora é gerenciado pelo tests/conftest.py
# que garante um banco gravável tanto em CI quanto localmente

from modules.database import init_database, get_db, ContaPagar, RegraM11, add_conta, get_regra, add_or_update_regra
from modules.pdf_parser import extract_from_pdf, ocr_status
from modules.logging_config import setup_logging
import logging
from datetime import datetime

setup_logging()
logger = logging.getLogger('test_runner')

def test_database_initialization():
    """Test 1: Database initialization"""
    logger.info('=== Test 1: Database Init ===')
    try:
        init_database()
        db = get_db()
        assert db is not None
        db.close()
        logger.info('✅ Database initialization OK')
    except Exception as e:
        logger.error(f'❌ Database init failed: {e}', exc_info=True)
        assert False, f"Database init failed: {e}"

def test_add_conta():
    """Test 2: Add conta to database"""
    logger.info('=== Test 2: Add Conta ===')
    try:
        conta_id = add_conta({
            'vencimento': '25/12/2025',
            'fornecedor': 'Teste Fornecedor LTDA',
            'cnpj': '12.345.678/0001-99',
            'categoria': 'Teste',
            'descricao': 'Conta de teste automatizado',
            'valor': 1500.00,
            'status': 'Pendente',
            'linha_digitavel': '12345.67890 12345.678901 12345.678901 1 12345678901234',
            'pdf_path': 'teste.pdf'
        })
        assert conta_id is not None
        logger.info(f'✅ Conta adicionada com ID: {conta_id}')
    except Exception as e:
        logger.error(f'❌ Add conta failed: {e}', exc_info=True)
        assert False, f"Add conta failed: {e}"

def test_regra_creation():
    """Test 3: Create and activate regra"""
    logger.info('=== Test 3: Regra Creation ===')
    try:
        cnpj_teste = '98.765.432/0001-10'
        # Adicionar 3 vezes para ativar
        for i in range(3):
            add_or_update_regra(cnpj_teste, f'Fornecedor Test {i+1}', 'Categoria Teste')
            logger.info(f'Regra registrada - uso {i+1}/3')
        
        regra = get_regra(cnpj_teste)
        assert regra is not None
        assert regra['ativo'] == True
        assert regra['contador_usos'] >= 3
        logger.info(f'✅ Regra ativada: {regra}')
    except Exception as e:
        logger.error(f'❌ Regra creation failed: {e}', exc_info=True)
        assert False, f"Regra creation failed: {e}"

def test_pdf_parser_fallback():
    """Test 4: PDF parser with sample data"""
    logger.info('=== Test 4: PDF Parser Fallback ===')
    try:
        # Simulate PDF with embedded text
        fake_pdf = b"""
        BOLETO BANCARIO
        CNPJ: 11.222.333/0001-44
        Vencimento: 30/12/2025
        Valor: R$ 2.500,00
        12345.67890 12345.678901 12345.678901 1 99887766554433
        """
        dados = extract_from_pdf(fake_pdf, filename='boleto_teste_11.222.333-0001-44.pdf')
        logger.info(f'OCR Status: {ocr_status()}')
        logger.info(f'Dados extraídos: {dados}')
        
        # Validate at least CNPJ from filename
        assert dados.get('cnpj') != '', f"CNPJ not extracted: {dados}"
        logger.info('✅ PDF parser working (fallback mode)')
    except Exception as e:
        logger.error(f'❌ PDF parser test failed: {e}', exc_info=True)
        assert False, f"PDF parser test failed: {e}"

def test_database_queries():
    """Test 5: Query operations"""
    logger.info('=== Test 5: Database Queries ===')
    try:
        db = get_db()
        contas = db.query(ContaPagar).all()
        regras = db.query(RegraM11).all()
        db.close()
        
        logger.info(f'Total contas: {len(contas)}')
        logger.info(f'Total regras: {len(regras)}')
        assert len(contas) >= 1, "No contas found"
        assert len(regras) >= 1, "No regras found"
        logger.info('✅ Database queries OK')
    except Exception as e:
        logger.error(f'❌ Database query failed: {e}', exc_info=True)
        assert False, f"Database query failed: {e}"

def run_all_tests():
    """Execute all tests and report results"""
    logger.info('\n' + '='*60)
    logger.info('🧪 INICIANDO TESTES AUTOMATIZADOS')
    logger.info('='*60 + '\n')
    
    tests = [
        test_database_initialization,
        test_add_conta,
        test_regra_creation,
        test_pdf_parser_fallback,
        test_database_queries
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append((test.__name__, result))
        except Exception as e:
            logger.error(f'CRITICAL ERROR in {test.__name__}: {e}', exc_info=True)
            results.append((test.__name__, False))
        logger.info('')
    
    logger.info('\n' + '='*60)
    logger.info('📊 RESULTADOS DOS TESTES')
    logger.info('='*60)
    
    passed = sum(1 for _, r in results if r)
    total = len(results)
    
    for name, result in results:
        status = '✅ PASS' if result else '❌ FAIL'
        logger.info(f'{status}: {name}')
    
    logger.info(f'\n🎯 Total: {passed}/{total} testes passaram')
    logger.info('='*60 + '\n')
    
    return passed == total

if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)
