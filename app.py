# app.py - Main Dashboard Hub Financeiro MLH
import streamlit as st
from dotenv import load_dotenv
import sys
import os
from datetime import datetime, timedelta

# Add project root to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import modules
from modules.config import get_tiny_auth, get_shopee_auth, get_logger
from modules.tiny_api import TinyERPAuth, TinyERPInvoiceFetcher, TinyERPPayables
from integrations.shopee.auth import ShopeeAuth
from integrations.shopee.orders import ShopeeOrders
from integrations.shopee.products import ShopeeProducts
from integrations.shopee.fees import ShopeeFees
from modules.pdf_processor import PDFBoletoProcessor
from modules.pdf_payables_integration import PDFPayablesIntegration

# Initialize logger
logger = get_logger("APP")

# Load environment variables
load_dotenv()

# Configure page
st.set_page_config(
    page_title="HUB Financeiro - MLH DEV",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Cache for API clients
@st.cache_resource
def init_tiny_client():
    try:
        return TinyERPAuth()
    except Exception as e:
        logger.error(f"Erro ao inicializar Tiny: {str(e)}")
        return None

@st.cache_resource
def init_shopee_client():
    try:
        return ShopeeAuth()
    except Exception as e:
        logger.error(f"Erro ao inicializar Shopee: {str(e)}")
        return None

# UI Theme
st.markdown("""
<style>
    .metric-card {
        background-color: #f0f2f6;
        padding: 20px;
        border-radius: 10px;
        margin: 10px 0;
    }
    .kpi-metric {
        font-size: 24px;
        font-weight: bold;
        color: #1f77b4;
    }
    .kpi-label {
        font-size: 14px;
        color: #666;
    }
</style>
""", unsafe_allow_html=True)

# Header
st.title("💰 HUB Financeiro – MLH DEV")
st.markdown("---")

# Sidebar - Navigation
with st.sidebar:
    st.header("⚙️ Configurações")
    
    # Status dos conectores
    st.subheader("Status dos Conectores")
    
    tiny_client = init_tiny_client()
    shopee_client = init_shopee_client()
    
    tiny_status = "✅ Ativo" if tiny_client else "❌ Inativo"
    shopee_status = "✅ Ativo" if shopee_client else "❌ Inativo"
    
    st.write(f"**Tiny ERP:** {tiny_status}")
    st.write(f"**Shopee:** {shopee_status}")
    
    st.divider()
    
    # Refresh interval
    st.subheader("Atualização de Dados")
    refresh_interval = st.select_slider(
        "Intervalo de atualização (minutos)",
        options=[5, 10, 15, 30, 60],
        value=15
    )
    
    if st.button("🔄 Atualizar Agora"):
        st.cache_resource.clear()
        st.rerun()

# Tabs
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📊 Visão Geral",
    "📋 Tiny ERP",
    "🛍️ Shopee",
    "📄 PDF Processor",
    "❓ Ajuda"
])

# TAB 1 - DASHBOARD OVERVIEW
with tab1:
    st.header("📊 Dashboard - Visão Geral")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="Contas a Pagar",
            value="--",
            help="Total de contas a pagar pendentes"
        )
    
    with col2:
        st.metric(
            label="Pedidos Shopee",
            value="--",
            help="Total de pedidos sincronizados"
        )
    
    with col3:
        st.metric(
            label="Produtos",
            value="--",
            help="Quantidade de produtos ativos"
        )
    
    with col4:
        st.metric(
            label="Taxa Média",
            value="--",
            help="Taxa média de processamento"
        )
    
    st.divider()
    
    # KPI Charts
    col_left, col_right = st.columns(2)
    
    with col_left:
        st.subheader("📈 Tendência de Contas a Pagar")
        st.info("Gráfico de tendência será preenchido com dados em tempo real")
    
    with col_right:
        st.subheader("💹 Composição por Fornecedor")
        st.info("Breakdown de contas por fornecedor")
    
    st.divider()
    
    # Recent activities
    st.subheader("📌 Atividades Recentes")
    st.info("Últimas operações serão exibidas aqui")

# TAB 2 - TINY ERP INTEGRATION
with tab2:
    st.header("📋 Integração Tiny ERP")
    
    tiny_tab1, tiny_tab2, tiny_tab3 = st.tabs([
        "🧾 Notas Fiscais",
        "💳 Contas a Pagar",
        "📊 Relatórios"
    ])
    
    with tiny_tab1:
        st.subheader("Notas Fiscais Emitidas")
        
        col1, col2 = st.columns([3, 1])
        with col1:
            date_range = st.date_input(
                "Período",
                value=(datetime.now() - timedelta(days=30), datetime.now())
            )
        with col2:
            if st.button("🔄 Sincronizar"):
                st.success("Sincronização iniciada...")
        
        if tiny_client:
            try:
                fetcher = TinyERPInvoiceFetcher(tiny_client)
                # Placeholder for data fetch
                st.info("Dados de NFs serão carregados aqui")
            except Exception as e:
                st.error(f"Erro ao carregar NFs: {str(e)}")
        else:
            st.warning("Conexão com Tiny ERP não disponível")
    
    with tiny_tab2:
        st.subheader("Contas a Pagar")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            status_filter = st.selectbox(
                "Filtrar por status",
                ["Todos", "Pendente", "Pago", "Atrasado"]
            )
        with col2:
            if st.button("➕ Nova Conta"):
                st.success("Formulário para nova conta será exibido")
        with col3:
            if st.button("📥 Importar PDF"):
                st.info("Upload de PDFs será processado")
        
        if tiny_client:
            try:
                payables = TinyERPPayables(tiny_client)
                st.info("Contas a pagar serão listadas aqui")
            except Exception as e:
                st.error(f"Erro ao carregar contas: {str(e)}")
        else:
            st.warning("Conexão com Tiny ERP não disponível")
    
    with tiny_tab3:
        st.subheader("Relatórios Financeiros")
        
        report_type = st.selectbox(
            "Tipo de relatório",
            ["Contas a Pagar por Vencimento", "Contas por Fornecedor", "Fluxo de Caixa"]
        )
        
        st.info(f"Relatório '{report_type}' será gerado aqui")

# TAB 3 - SHOPEE INTEGRATION
with tab3:
    st.header("🛍️ Integração Shopee")
    
    shopee_tab1, shopee_tab2, shopee_tab3 = st.tabs([
        "📦 Pedidos",
        "🏷️ Produtos",
        "💰 Taxas"
    ])
    
    with shopee_tab1:
        st.subheader("Pedidos Recentes")
        
        col1, col2 = st.columns([3, 1])
        with col1:
            date_range = st.date_input(
                "Período",
                value=(datetime.now() - timedelta(days=7), datetime.now()),
                key="shopee_order_dates"
            )
        with col2:
            if st.button("🔄 Sincronizar Pedidos"):
                st.success("Sincronização de pedidos iniciada...")
        
        if shopee_client:
            try:
                orders = ShopeeOrders(shopee_client)
                st.info("Lista de pedidos será exibida aqui")
            except Exception as e:
                st.error(f"Erro ao carregar pedidos: {str(e)}")
        else:
            st.warning("Conexão com Shopee não disponível")
    
    with shopee_tab2:
        st.subheader("Catálogo de Produtos")
        
        col1, col2 = st.columns([2, 1])
        with col1:
            search_term = st.text_input("🔍 Buscar produtos")
        with col2:
            if st.button("🔄 Sincronizar Produtos"):
                st.success("Sincronização de produtos iniciada...")
        
        if shopee_client:
            try:
                products = ShopeeProducts(shopee_client)
                st.info("Catálogo de produtos será exibido aqui")
            except Exception as e:
                st.error(f"Erro ao carregar produtos: {str(e)}")
        else:
            st.warning("Conexão com Shopee não disponível")
    
    with shopee_tab3:
        st.subheader("Análise de Taxas")
        
        if st.button("📊 Calcular Taxas"):
            st.success("Cálculo de taxas iniciado...")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Taxa Média de Comissão", "5.5%", "-0.5%")
        with col2:
            st.metric("Taxa de Processamento", "2.0%", "+0.0%")
        with col3:
            st.metric("Taxa Total Média", "7.5%", "-0.5%")
        
        st.info("Detalhamento de taxas por categoria será exibido aqui")

# TAB 4 - PDF PROCESSOR
with tab4:
    st.header("📄 Processador de Boletos PDF")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        uploaded_files = st.file_uploader(
            "📤 Selecione arquivo(s) PDF para processar",
            type="pdf",
            accept_multiple_files=True,
            help="Arquivos de boletos para extração de dados"
        )
    
    with col2:
        if st.button("⚙️ Processar"):
            if uploaded_files:
                st.info("Processamento iniciado...")
            else:
                st.warning("Selecione ao menos um arquivo PDF")
    
    if uploaded_files:
        st.subheader(f"📋 {len(uploaded_files)} arquivo(s) selecionado(s)")
        
        for uploaded_file in uploaded_files:
            with st.expander(f"📄 {uploaded_file.name}"):
                # Save temp file
                temp_path = f"/tmp/{uploaded_file.name}"
                os.makedirs(os.path.dirname(temp_path), exist_ok=True)
                
                with open(temp_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                
                try:
                    # Process PDF
                    processor = PDFBoletoProcessor()
                    boleto_data = processor.extract_boleto_data(temp_path)
                    
                    if boleto_data.get("dados_extraidos"):
                        st.success("✅ Dados extraídos com sucesso!")
                        
                        extracted = boleto_data["dados_extraidos"]
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            st.metric("Valor", extracted.get("valor", "N/A"))
                            st.metric("Cedente", extracted.get("cedente", "N/A")[:30])
                        with col2:
                            st.metric("Vencimento", extracted.get("vencimento", "N/A"))
                            st.metric("Banco", extracted.get("banco", "N/A"))
                        
                        # Option to send to Tiny ERP
                        if st.button(f"📤 Enviar para Tiny ERP", key=f"send_{uploaded_file.name}"):
                            try:
                                if tiny_client:
                                    pdf_integration = PDFPayablesIntegration(tiny_client)
                                    result = pdf_integration.extract_and_prefill(temp_path)
                                    
                                    if result.get("status") == "sucesso":
                                        st.success(f"✅ Conta criada com sucesso! ID: {result.get('payable_criada', {}).get('id', 'N/A')}")
                                    else:
                                        st.error(f"❌ Erro: {result.get('mensagem', 'Erro desconhecido')}")
                                else:
                                    st.warning("Conexão com Tiny ERP não disponível")
                            except Exception as e:
                                st.error(f"❌ Erro ao enviar: {str(e)}")
                    else:
                        st.warning("⚠️ Nenhum dado de boleto foi extraído do arquivo")
                
                except Exception as e:
                    st.error(f"❌ Erro ao processar PDF: {str(e)}")
                finally:
                    # Clean up temp file
                    if os.path.exists(temp_path):
                        os.remove(temp_path)
    
    st.divider()
    st.subheader("📊 Histórico de Processamento")
    st.info("Últimos arquivos processados serão exibidos aqui")

# TAB 5 - HELP
with tab5:
    st.header("❓ Ajuda e Documentação")
    
    st.subheader("🚀 Como Começar")
    st.markdown("""
    ### 1. Configurar Credenciais
    - Copie o arquivo `.env.example` para `.env`
    - Preencha com suas chaves de API:
      - **Tiny ERP**: Token de acesso
      - **Shopee**: Shop ID e Partner ID + Secret
    
    ### 2. Sincronizar Dados
    - Acesse **Tiny ERP** para sincronizar notas fiscais
    - Acesse **Shopee** para buscar pedidos e produtos
    
    ### 3. Processar Boletos
    - Vá a **PDF Processor**
    - Faça upload de arquivos boleto
    - Exporte dados para Tiny ERP
    
    ### 4. Monitorar Dashboard
    - Visualize KPIs em tempo real
    - Acompanhe taxas e receitas
    """)
    
    st.divider()
    
    st.subheader("🔗 Links Úteis")
    st.markdown("""
    - [Documentação Tiny ERP](https://tiny.com.br/)
    - [API Shopee](https://shopee.com.br/)
    - [GitHub do Projeto](https://github.com/mlhutilidades-star/projetomlh)
    - [README](https://github.com/mlhutilidades-star/projetomlh/blob/master/README.md)
    """)
    
    st.divider()
    
    st.subheader("💬 Suporte")
    st.write("Para dúvidas ou problemas, abra uma issue no GitHub do projeto.")

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; padding: 20px; color: #999; font-size: 12px;">
    <p>HUB Financeiro – MLH DEV | Desenvolvido com ❤️</p>
    <p>Última atualização: """ + datetime.now().strftime("%d/%m/%Y %H:%M:%S") + """</p>
</div>
""", unsafe_allow_html=True)
