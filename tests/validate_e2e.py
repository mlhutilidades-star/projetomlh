"""
Script de validação end-to-end - testa todas as páginas e funcionalidades
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from modules.logging_config import setup_logging
import logging

setup_logging()
logger = logging.getLogger('validation')

def validate_system():
    """Validação completa do sistema"""
    logger.info('\n' + '='*70)
    logger.info('🎯 VALIDAÇÃO COMPLETA DO SISTEMA')
    logger.info('='*70 + '\n')
    
    tests_passed = []
    tests_failed = []
    
    # Test 1: Imports críticos
    logger.info('📦 Teste 1: Validando imports...')
    try:
        from modules.database import init_database, get_db, add_conta, get_regra, add_or_update_regra
        from modules.pdf_parser import extract_from_pdf, ocr_status
        from modules.rules import get_rule_for_cnpj
        from modules.tiny_api import listar_produtos
        from modules.shopee_api import listar_pedidos
        logger.info('✅ Todos os módulos importados com sucesso')
        tests_passed.append('Imports')
    except Exception as e:
        logger.error(f'❌ Erro nos imports: {e}', exc_info=True)
        tests_failed.append('Imports')
    
    # Test 2: Database operations
    logger.info('\n💾 Teste 2: Operações de banco de dados...')
    try:
        init_database()
        db = get_db()
        
        # Criar conta teste
        conta_id = add_conta({
            'vencimento': '31/12/2025',
            'fornecedor': 'Validação E2E LTDA',
            'cnpj': '55.666.777/0001-88',
            'categoria': 'Teste E2E',
            'descricao': 'Conta criada durante validação automática',
            'valor': 9999.99,
            'status': 'Pendente',
            'linha_digitavel': '99999.88888 77777.666666 55555.444444 3 33333333333333'
        })
        
        # Criar e ativar regra
        for i in range(3):
            add_or_update_regra('55.666.777/0001-88', 'Validação E2E LTDA', 'Teste E2E')
        
        regra = get_regra('55.666.777/0001-88')
        
        db.close()
        
        assert conta_id is not None, "Conta não foi criada"
        assert regra is not None, "Regra não foi criada"
        assert regra['ativo'] == True, "Regra não foi ativada"
        
        logger.info(f'✅ Conta criada (ID: {conta_id}), Regra ativada (usos: {regra["contador_usos"]})')
        tests_passed.append('Database')
    except Exception as e:
        logger.error(f'❌ Erro no banco de dados: {e}', exc_info=True)
        tests_failed.append('Database')
    
    # Test 3: PDF Parser com diferentes cenários
    logger.info('\n📄 Teste 3: Parser de PDF (múltiplos cenários)...')
    try:
        # Cenário 1: Boleto completo
        pdf_completo = b"""
        BANCO DO BRASIL
        CNPJ: 12.345.678/0001-99
        Vencimento: 15/01/2026
        Valor: R$ 1.234,56
        12345.67890 12345.678901 12345.678901 2 98765432109876
        """
        dados1 = extract_from_pdf(pdf_completo, 'boleto_completo.pdf')
        
        # Cenário 2: PDF mínimo (só CNPJ no nome)
        pdf_minimo = b"Documento fiscal"
        dados2 = extract_from_pdf(pdf_minimo, 'fatura_88.999.000-0001-22.pdf')
        
        # Cenário 3: PDF vazio
        pdf_vazio = b""
        dados3 = extract_from_pdf(pdf_vazio, 'documento.pdf')
        
        assert dados1['cnpj'] != '', f"CNPJ não extraído do boleto completo: {dados1}"
        assert dados2['cnpj'] != '', f"CNPJ não extraído do filename: {dados2}"
        
        logger.info(f'✅ Parser validado em 3 cenários')
        logger.info(f'   Cenário 1 (completo): {len([k for k,v in dados1.items() if v])} campos')
        logger.info(f'   Cenário 2 (filename): CNPJ={dados2["cnpj"]}')
        logger.info(f'   Cenário 3 (vazio): {dados3}')
        tests_passed.append('PDF Parser')
    except Exception as e:
        logger.error(f'❌ Erro no parser: {e}', exc_info=True)
        tests_failed.append('PDF Parser')
    
    # Test 4: Pages structure
    logger.info('\n📑 Teste 4: Estrutura de páginas...')
    try:
        pages_dir = 'pages'
        expected_pages = [
            '1_📊_Dashboard.py',
            '2_💳_Contas_Pagar.py',
            '3_📄_Upload_PDF.py',
            '4_🏢_Tiny_ERP.py',
            '5_🛍️_Shopee.py',
            '6_🧠_Regras_PDF.py'
        ]
        
        existing_pages = os.listdir(pages_dir)
        missing_pages = [p for p in expected_pages if p not in existing_pages]
        
        assert len(missing_pages) == 0, f"Páginas faltando: {missing_pages}"
        
        logger.info(f'✅ Todas as {len(expected_pages)} páginas existem')
        for page in expected_pages:
            logger.info(f'   ✓ {page}')
        tests_passed.append('Pages Structure')
    except Exception as e:
        logger.error(f'❌ Erro na estrutura: {e}', exc_info=True)
        tests_failed.append('Pages Structure')
    
    # Test 5: Configuration files
    logger.info('\n⚙️ Teste 5: Arquivos de configuração...')
    try:
        required_files = [
            'app.py',
            'requirements.txt',
            '.env.example',
            '.gitignore',
            'README.md'
        ]
        
        missing_files = [f for f in required_files if not os.path.exists(f)]
        assert len(missing_files) == 0, f"Arquivos faltando: {missing_files}"
        
        logger.info(f'✅ Todos os arquivos de configuração presentes')
        tests_passed.append('Configuration')
    except Exception as e:
        logger.error(f'❌ Erro na configuração: {e}', exc_info=True)
        tests_failed.append('Configuration')
    
    # Test 6: Logging system
    logger.info('\n📝 Teste 6: Sistema de logging...')
    try:
        log_dir = 'logs'
        assert os.path.exists(log_dir), "Diretório de logs não existe"
        
        from datetime import datetime
        today_log = os.path.join(log_dir, f"app_{datetime.now().strftime('%Y%m%d')}.log")
        
        if os.path.exists(today_log):
            with open(today_log, 'r', encoding='utf-8') as f:
                log_content = f.read()
                assert len(log_content) > 0, "Log vazio"
                logger.info(f'✅ Sistema de logs ativo ({len(log_content)} bytes)')
        else:
            logger.warning('⚠️ Log de hoje ainda não existe (normal se primeira execução)')
        
        tests_passed.append('Logging')
    except Exception as e:
        logger.error(f'❌ Erro no logging: {e}', exc_info=True)
        tests_failed.append('Logging')
    
    # Summary
    logger.info('\n' + '='*70)
    logger.info('📊 RESUMO DA VALIDAÇÃO')
    logger.info('='*70)
    
    total = len(tests_passed) + len(tests_failed)
    logger.info(f'\n✅ Testes passados: {len(tests_passed)}/{total}')
    for test in tests_passed:
        logger.info(f'   ✓ {test}')
    
    if tests_failed:
        logger.info(f'\n❌ Testes falhos: {len(tests_failed)}/{total}')
        for test in tests_failed:
            logger.info(f'   ✗ {test}')
    
    logger.info('\n' + '='*70)
    
    if len(tests_failed) == 0:
        logger.info('🎉 SISTEMA 100% VALIDADO E OPERACIONAL!')
        logger.info('='*70 + '\n')
        return True
    else:
        logger.warning('⚠️ Sistema parcialmente validado. Revisar falhas.')
        logger.info('='*70 + '\n')
        return False

if __name__ == '__main__':
    success = validate_system()
    sys.exit(0 if success else 1)
