"""
Guia do Usuário - Ajuda e Documentação
"""
import streamlit as st

st.set_page_config(page_title="Ajuda", page_icon="❓", layout="wide")
st.title("❓ Guia do Usuário")

# Tabs para diferentes seções
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "🚀 Início Rápido",
    "📋 Contas a Pagar",
    "📄 Upload de PDF",
    "🧠 Regras M11",
    "🔧 Integrações"
])

with tab1:
    st.header("🚀 Início Rápido")
    
    st.markdown("""
    ### Bem-vindo ao Hub Financeiro!
    
    Este sistema foi desenvolvido para facilitar a gestão financeira da sua empresa com recursos de:
    - ✅ Cadastro manual e automático de contas
    - 📄 Extração inteligente de dados de boletos
    - 🤖 Aprendizado automático de padrões (Regras M11)
    - 📊 Dashboards e relatórios
    - 🔗 Integrações com Tiny ERP e Shopee
    
    ---
    
    ### Primeiros Passos
    
    **1. Configure as Credenciais**
    - Edite o arquivo `.env` na raiz do projeto
    - Adicione tokens de API (Tiny, Shopee) se desejar usar integrações
    - As funcionalidades principais funcionam sem integrações
    
    **2. Explore o Dashboard**
    - Acesse "📊 Dashboard" no menu lateral
    - Veja estatísticas, gráficos e alertas
    
    **3. Cadastre sua Primeira Conta**
    - Vá para "💳 Contas a Pagar"
    - Preencha o formulário ou faça upload de um PDF
    
    **4. Veja os Alertas**
    - Acesse "🔔 Alertas" para ver vencimentos próximos
    - Acompanhe contas vencidas e vencendo
    """)
    
    st.info("""
    💡 **Dica:** Ative o "Debug Mode" no menu lateral para ver status do sistema em tempo real!
    """)

with tab2:
    st.header("📋 Gestão de Contas a Pagar")
    
    st.markdown("""
    ### Como Funciona
    
    A página **"💳 Contas a Pagar"** possui duas abas principais:
    
    #### 📋 Lista de Contas
    - Visualize todas as contas cadastradas
    - Filtre por mês, status ou busque por fornecedor/categoria
    - Veja estatísticas de valor total
    - **Exporte para Excel** clicando no botão de exportação
    
    #### ➕ Nova Conta
    
    **Método 1: Upload de Boleto (Recomendado)**
    1. Na seção "📄 Anexar Boleto (PDF)", clique em "Browse files"
    2. Selecione o PDF do boleto
    3. O sistema extrai automaticamente:
       - CNPJ do fornecedor
       - Valor
       - Data de vencimento
       - Linha digitável
    4. Revise os campos preenchidos
    5. Ajuste se necessário
    6. Clique em "💾 Salvar Conta"
    
    **Método 2: Prefill por CNPJ**
    1. Digite o CNPJ no campo "CNPJ para buscar regra"
    2. Se houver regra ativa, fornecedor e categoria são preenchidos automaticamente
    3. Complete os demais campos
    4. Salve a conta
    
    **Método 3: Cadastro Manual**
    1. Preencha todos os campos manualmente
    2. Campos obrigatórios: Vencimento, Fornecedor, Valor
    3. Salve a conta
    
    ---
    
    ### Recursos Avançados
    
    **Detecção de Duplicatas**
    - Ao salvar, o sistema verifica se já existe conta similar
    - Compara: fornecedor + valor + vencimento (±3 dias)
    - Alerta antes de criar duplicata
    
    **Normalização Automática**
    - CNPJs são formatados automaticamente
    - Aceita diversos formatos: `12345678000199`, `12.345.678/0001-99`, etc.
    """)

with tab3:
    st.header("📄 Upload e Extração de PDF")
    
    st.markdown("""
    ### Tecnologia de Extração
    
    O sistema usa **dois modos** de extração:
    
    **1. OCR Completo (Tesseract + Poppler)**
    - Extrai texto de imagens e PDFs escaneados
    - Maior precisão
    - Requer instalação de dependências externas
    
    **2. Fallback Simples (Padrão)**
    - Usa regex sobre bytes do arquivo e nome
    - Funciona sem dependências adicionais
    - Ideal para PDFs com texto nativo
    
    ---
    
    ### Instalação do OCR (Opcional)
    
    **Windows (PowerShell):**
    ```powershell
    # Via Chocolatey
    choco install tesseract -y
    choco install poppler -y
    ```
    
    **Verificação:**
    - Ative "Debug Mode" no sidebar
    - Veja o status OCR
    
    ---
    
    ### Dados Extraídos
    
    O parser tenta identificar:
    - ✅ **CNPJ**: Formato `XX.XXX.XXX/XXXX-XX` ou similar
    - ✅ **Valor**: Padrão `R$ X.XXX,XX`
    - ✅ **Vencimento**: Formato `DD/MM/AAAA`
    - ✅ **Linha Digitável**: Sequência numérica do boleto
    
    Se um campo não for encontrado, você pode preencher manualmente.
    
    ---
    
    ### Formatos Aceitos
    - ✅ PDF (.pdf)
    - ✅ Todos os tamanhos
    - ✅ PDFs nativos ou escaneados
    """)

with tab4:
    st.header("🧠 Sistema de Regras M11")
    
    st.markdown("""
    ### O que são Regras M11?
    
    O sistema **aprende automaticamente** padrões de fornecedores com base no CNPJ.
    Após **3 cadastros** com o mesmo CNPJ, a regra é **ativada**.
    
    ---
    
    ### Como Funciona
    
    **1. Cadastro Inicial**
    - Você cadastra uma conta com CNPJ `12.345.678/0001-99`
    - Fornecedor: "Fornecedor ABC"
    - Categoria: "Energia"
    - Uma regra é criada com **1 uso**
    
    **2. Segundo Cadastro**
    - Mesmo CNPJ, mesmo fornecedor e categoria
    - Regra atualizada: **2 usos**
    
    **3. Terceiro Cadastro**
    - Mesmo CNPJ
    - Regra **ativada automaticamente** ✅
    
    **4. Próximos Cadastros**
    - Ao digitar o CNPJ, fornecedor e categoria são preenchidos automaticamente
    - Economiza tempo!
    
    ---
    
    ### Gerenciar Regras
    
    Acesse **"🧠 Regras PDF"** para:
    - Ver todas as regras cadastradas
    - Editar fornecedor ou categoria
    - Ativar/desativar regras manualmente
    - Ver contador de usos
    
    ---
    
    ### Dicas
    
    💡 **Consistência é importante**: Use sempre o mesmo fornecedor e categoria para o mesmo CNPJ
    
    💡 **Correções**: Se errou o fornecedor, edite a regra na página de gerenciamento
    
    💡 **Desativação**: Desative regras temporariamente sem perder o histórico
    """)

with tab5:
    st.header("🔧 Integrações")
    
    st.markdown("""
    ### Tiny ERP
    
    **O que faz:**
    - Lista produtos cadastrados
    - Busca pedidos
    - Consulta contas a pagar (futuro)
    
    **Configuração:**
    1. Obtenha seu token na área de desenvolvedores do Tiny
    2. Adicione ao `.env`:
       ```
       TINY_API_TOKEN=seu_token_aqui
       ```
    3. Reinicie o Streamlit
    4. Acesse "🏢 Tiny ERP" no menu
    
    **Página Tiny ERP:**
    - Ver produtos cadastrados
    - Buscar por nome/código
    - Paginação automática
    
    ---
    
    ### Shopee
    
    **O que faz:**
    - Lista pedidos da loja
    - Sincroniza vendas
    - Acompanha status de pedidos
    
    **Configuração:**
    1. Registre seu app no Shopee Developer Portal
    2. Obtenha: Partner ID, Partner Key, Shop ID
    3. Adicione ao `.env`:
       ```
       SHOPEE_PARTNER_ID=seu_id
       SHOPEE_PARTNER_KEY=sua_key
       SHOPEE_SHOP_ID=seu_shop_id
       ```
    4. Reinicie o Streamlit
    5. Acesse "🛍️ Shopee" no menu
    
    **Autenticação:**
    - Usa assinatura HMAC SHA256
    - Tokens válidos por requisição
    - Seguro e auditável
    
    ---
    
    ### Logs e Monitoramento
    
    Todos os logs de integração ficam em:
    - `logs/app_YYYYMMDD.log`
    
    Veja erros e debug de APIs no arquivo de log.
    """)

# Quick reference
st.markdown("---")
st.subheader("⚡ Referência Rápida")

col1, col2 = st.columns(2)

with col1:
    st.markdown("""
    **Atalhos e Recursos:**
    - 📊 Dashboard: Visão geral completa
    - 💳 Contas a Pagar: Cadastro e listagem
    - 📄 Upload PDF: Extração automática
    - 🧠 Regras: Gerenciar aprendizado
    - 🏢 Tiny: Integração ERP
    - 🛍️ Shopee: Marketplace
    - 📥 Importação: Upload em lote
    - 🔔 Alertas: Vencimentos próximos
    """)

with col2:
    st.markdown("""
    **Suporte:**
    - 📝 Logs: `logs/app_YYYYMMDD.log`
    - 🐛 Debug Mode: Ativar no sidebar
    - ✅ Validação: `python tests/validate_e2e.py`
    - 🧪 Testes: `python tests/test_runner.py`
    - 🤖 Auto-healer: `python auto_healer.py`
    """)

# Version info
st.markdown("---")
st.caption("Hub Financeiro v1.0.0 | Desenvolvido com Streamlit + Python")
