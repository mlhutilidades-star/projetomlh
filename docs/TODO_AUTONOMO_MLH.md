# TODO AUTÔNOMO MLH

## Funcionalidades Principais

- [ ] Contas a Pagar
  - [ ] Cadastro de contas
  - [ ] Edição de contas
  - [ ] Exclusão de contas
  - [ ] Marcação como paga
  - [ ] Listagem de contas pendentes/pagas

- [ ] Leitura de PDF
  - [ ] Extração de dados de boletos
  - [ ] Extração de dados de notas fiscais
  - [ ] Associação automática com contas

- [ ] Integração Tiny ERP
  - [ ] Autenticação e conexão com API Tiny
  - [ ] Sincronização de dados financeiros
  - [ ] Sincronização de estoque

- [ ] Integração Shopee
  - [ ] Autenticação e conexão com API Shopee
  - [ ] Importação de vendas/pedidos

- [ ] Dashboard
  - [ ] Visualização de contas a pagar
  - [ ] Gráficos de receitas/despesas
  - [ ] Indicadores principais

## Técnicos

- [x] Estruturação do banco de dados (modelagem inicial planejada)
- [ ] Configuração do backend (API)
- [ ] Configuração do frontend (Streamlit)
- [x] Documentação dos módulos
- [ ] Testes automatizados

### Próximo passo

- Criar a modelagem inicial do banco de dados para Contas a Pagar (tabela: contas_pagar) com os campos essenciais:
  - id (inteiro, chave primária)
  - descricao (texto)
  - valor (decimal)
  - data_vencimento (data)
  - status (pago/pendente)
  - data_pagamento (data, opcional)
  - fornecedor (texto, opcional)
