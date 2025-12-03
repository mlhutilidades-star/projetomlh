# Especificação do Projeto MLH

## Objetivo
O projeto MLH visa criar um sistema autônomo para gestão financeira, incluindo:
- Contas a Pagar
- Leitura de PDF de notas fiscais e boletos
- Integração com Tiny ERP
- Integração com Shopee
- Dashboard básico para visualização de dados

## Funcionalidades Principais

### 1. Contas a Pagar
- Cadastro de contas a pagar
- Edição e exclusão de contas
- Marcação de contas como pagas
- Visualização de contas pendentes e pagas

### 2. Leitura de PDF
- Extração automática de dados de boletos e notas fiscais em PDF
- Associação dos dados extraídos às contas a pagar

### 3. Integração Tiny ERP
- Sincronização de dados financeiros e de estoque com o Tiny ERP

### 4. Integração Shopee
- Importação de vendas e pedidos da Shopee

### 5. Dashboard
- Visualização gráfica de contas, receitas, despesas e indicadores principais

## Requisitos Técnicos
- Backend em Python (preferencialmente FastAPI ou Flask)
- Frontend em Streamlit
- Banco de dados SQLite ou PostgreSQL
- Integração com APIs externas (Tiny, Shopee)
- Leitura de PDF com PyPDF2, pdfplumber ou similar

## Usuários
- Administrador
- Usuário comum

## Segurança
- Autenticação básica
- Permissões por perfil

## Observações
- O sistema deve ser modular e de fácil manutenção.
- Documentação clara para cada módulo.
