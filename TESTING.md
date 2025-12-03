# Arquitetura de Testes - MLH Hub Financeiro

## Visão Geral

Suite completa de testes automatizados com **86 testes** cobrindo 55% do código base.

## Estrutura de Testes

### Unit Tests (Testes Unitários)
Testes isolados de funções e classes individuais sem dependências externas.

- `test_utils.py` / `test_utils_expanded.py` - Funções utilitárias (formatação, limpeza)
- `test_validation.py` / `test_validation_expanded.py` - Validação de CNPJ, parsing de valores e datas
- `test_rules.py` - Lógica de regras de negócio
- `test_domain_entities.py` - Entidades de domínio
- `test_repositories.py` - Repositórios de dados
- `test_services.py` - Camada de serviços
- `test_nfe_generator.py` - Geração de NFe
- `test_nfe_ipi_formula.py` - Cálculos de IPI

### Integration Tests (Testes de Integração)
Testes com mocks de APIs externas e bancos de dados.

- `test_shopee_integration.py` - Cliente Shopee API (autenticação, produtos, assinaturas HMAC)
- `test_tiny_integration.py` - Cliente Tiny ERP (produtos, NFe, parsing de valores brasileiros)
- `test_sync_apis.py` - Orquestração de sincronização (Shopee pedidos)
- `test_database.py` - Operações de banco de dados

### E2E Tests (Testes End-to-End)
Fluxos completos do sistema mockados.

- `test_e2e_pdf_workflow.py` - PDF → parsing → conta → registro
- `test_contas_pagar.py` - CRUD completo FastAPI

## Executar Testes

```bash
# Suite completa
pytest

# Com cobertura
pytest --cov=modules --cov-report=html

# Apenas testes rápidos
pytest -m "not slow"

# Testes específicos
pytest tests/test_validation_expanded.py -v

# Com output detalhado
pytest -v -s
```

## Métricas de Cobertura

| Módulo | Cobertura | Status |
|--------|-----------|--------|
| config.py | 100% | ✅ |
| domain/entities.py | 100% | ✅ |
| rules.py | 100% | ✅ |
| nfe_generator.py | 95% | ✅ |
| nfe_parser.py | 90% | ✅ |
| services.py | 79% | ⚠️ |
| pdf_parser.py | 78% | ⚠️ |
| database.py | 72% | ⚠️ |
| export_utils.py | 72% | ⚠️ |
| validation.py | 65% | ⚠️ |
| utils.py | 60% | ⚠️ |
| shopee_api.py | 48% | ❌ |
| sync_apis.py | 49% | ❌ |
| tiny_api.py | 24% | ❌ |

## Fixtures e Mocks

### Configuração Base
- `conftest.py` - Setup de sys.path e fixtures globais

### Mocks Principais
- APIs externas: `@patch('requests.get')`
- Configuração: `@patch('modules.config.SHOPEE_ACCESS_TOKEN')`
- Banco de dados: `@patch('modules.database.get_engine')`

## Próximas Melhorias

1. **Aumentar cobertura** para 70%+ nos módulos críticos (tiny_api, shopee_api, sync_apis)
2. **Fixtures reutilizáveis** em conftest.py (DB mock, API clients, sample data)
3. **Testes de stress** para endpoints FastAPI (load testing)
4. **CI/CD** com GitHub Actions rodando testes automaticamente
5. **Snapshot testing** para outputs de NFe e PDF parsing
6. **Property-based testing** com Hypothesis para validações

## Convenções

- Prefixo `test_` para funções de teste
- Docstrings descritivas em cada teste
- Arrange-Act-Assert pattern
- Mocks isolados por teste (não compartilhados)
- Nomes de teste expressivos: `test_<funcao>_<cenario>_<resultado_esperado>`
