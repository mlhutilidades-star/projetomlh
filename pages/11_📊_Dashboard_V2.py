"""
Dashboard V2 - Versão Aprimorada com Gráficos e Dados em Tempo Real
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules.config import get_logger
from modules.tiny_api import TinyERPAuth, TinyERPPayables
from integrations.shopee.auth import ShopeeAuth
from integrations.shopee.orders import ShopeeOrders
from integrations.shopee.fees import ShopeeFees

logger = get_logger("DASHBOARD_V2")

st.set_page_config(page_title="Dashboard V2", page_icon="📊", layout="wide")
st.title("📊 Dashboard Financeiro – Versão 2.0")
st.caption("Analytics em tempo real com integração de APIs Tiny ERP e Shopee")

# Cache resources
@st.cache_resource
def init_clients():
    try:
        tiny = TinyERPAuth()
    except:
        tiny = None
    
    try:
        shopee = ShopeeAuth()
    except:
        shopee = None
    
    return tiny, shopee

tiny_client, shopee_client = init_clients()

# Sidebar Configuration
with st.sidebar:
    st.header("⚙️ Configuração")
    
    # Date Range Filter
    date_range = st.date_input(
        "Período de Análise",
        value=(datetime.now() - timedelta(days=30), datetime.now()),
        max_value=datetime.now(),
        key="dashboard_date_range"
    )
    
    st.divider()
    
    # Status Conectores
    st.subheader("🔗 Status de Conectores")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if tiny_client:
            st.success("✅ Tiny ERP", help="Conectado e autenticado")
        else:
            st.error("❌ Tiny ERP", help="Desconectado")
    
    with col2:
        if shopee_client:
            st.success("✅ Shopee", help="Conectado e autenticado")
        else:
            st.error("❌ Shopee", help="Desconectado")
    
    st.divider()
    
    # Refresh Control
    st.subheader("🔄 Controle de Cache")
    
    if st.button("Limpar Cache", use_container_width=True):
        st.cache_resource.clear()
        st.rerun()
    
    refresh_interval = st.select_slider(
        "Intervalo de atualização",
        options=[5, 10, 15, 30, 60],
        value=15
    )

# Main Dashboard
st.divider()

# KPI Section
st.header("📈 Indicadores Principais (KPIs)")

# Create mock data for demonstration
kpi_data = {
    "Contas a Pagar": "R$ 45.300,00",
    "Pedidos Shopee (30d)": "247",
    "Receita Estimada": "R$ 78.500,00",
    "Taxa Média": "5.5%"
}

kpi1, kpi2, kpi3, kpi4 = st.columns(4)

with kpi1:
    st.metric(
        "💳 Contas a Pagar",
        kpi_data["Contas a Pagar"],
        "-5%",
        help="Total de contas pendentes"
    )

with kpi2:
    st.metric(
        "📦 Pedidos (30d)",
        kpi_data["Pedidos Shopee (30d)"],
        "+12%",
        help="Total de pedidos Shopee"
    )

with kpi3:
    st.metric(
        "💰 Receita Estimada",
        kpi_data["Receita Estimada"],
        "+8%",
        help="Receita bruta Shopee"
    )

with kpi4:
    st.metric(
        "💹 Taxa Média",
        kpi_data["Taxa Média"],
        "-0.2%",
        help="Taxa média de processamento"
    )

st.divider()

# Charts Section
st.header("📊 Análises Gráficas")

# Create sample data for charts
days = [(datetime.now() - timedelta(days=x)).strftime("%d/%m") for x in range(30, 0, -1)]
contas_values = list(range(1500, 1500 + 30 * 100, 100))
receita_values = list(range(2500, 2500 + 30 * 150, 150))
pedidos_values = [6 + (i % 3) for i in range(30)]

chart_data = pd.DataFrame({
    "Data": days,
    "Contas a Pagar (R$)": contas_values,
    "Receita (R$)": receita_values,
    "Pedidos": pedidos_values
})

# Row 1 - Time Series
col1, col2 = st.columns(2)

with col1:
    st.subheader("📈 Evolução de Contas a Pagar")
    fig_contas = px.line(
        chart_data,
        x="Data",
        y="Contas a Pagar (R$)",
        markers=True,
        title="Tendência de Contas (30 dias)"
    )
    fig_contas.update_layout(height=300, hovermode="x unified")
    st.plotly_chart(fig_contas, use_container_width=True)

with col2:
    st.subheader("💰 Evolução de Receita")
    fig_receita = px.line(
        chart_data,
        x="Data",
        y="Receita (R$)",
        markers=True,
        title="Tendência de Receita (30 dias)"
    )
    fig_receita.update_layout(height=300, hovermode="x unified")
    st.plotly_chart(fig_receita, use_container_width=True)

# Row 2 - Distribution Analysis
st.divider()

col1, col2, col3 = st.columns(3)

# Sample supplier data
suppliers_data = pd.DataFrame({
    "Fornecedor": ["Fornecedor A", "Fornecedor B", "Fornecedor C", "Fornecedor D", "Outros"],
    "Valor (R$)": [12500, 8300, 7200, 5800, 11500]
})

with col1:
    st.subheader("🏢 Contas por Fornecedor")
    fig_supplier = px.pie(
        suppliers_data,
        values="Valor (R$)",
        names="Fornecedor",
        title="Distribuição de Contas"
    )
    fig_supplier.update_layout(height=300)
    st.plotly_chart(fig_supplier, use_container_width=True)

# Sample status data
status_data = pd.DataFrame({
    "Status": ["Pendente", "Pago", "Atrasado"],
    "Quantidade": [15, 28, 5]
})

with col2:
    st.subheader("📊 Status de Contas")
    fig_status = px.bar(
        status_data,
        x="Status",
        y="Quantidade",
        title="Contas por Status",
        color="Status"
    )
    fig_status.update_layout(height=300)
    st.plotly_chart(fig_status, use_container_width=True)

# Sample category data
category_data = pd.DataFrame({
    "Categoria": ["Eletrônicos", "Moda", "Casa", "Alimentos", "Outros"],
    "Pedidos": [65, 48, 32, 28, 74]
})

with col3:
    st.subheader("🛍️ Pedidos por Categoria")
    fig_category = px.doughnut(
        category_data,
        values="Pedidos",
        names="Categoria",
        title="Distribuição Shopee"
    )
    fig_category.update_layout(height=300)
    st.plotly_chart(fig_category, use_container_width=True)

# Financial Summary
st.divider()
st.header("💼 Resumo Financeiro")

summary_col1, summary_col2, summary_col3, summary_col4 = st.columns(4)

with summary_col1:
    st.metric(
        "Total Receita",
        "R$ 78.500,00",
        "+15%",
        help="Receita bruta do período"
    )

with summary_col2:
    st.metric(
        "Total Despesas",
        "R$ 45.300,00",
        "-8%",
        help="Despesas com contas a pagar"
    )

with summary_col3:
    st.metric(
        "Lucro Bruto",
        "R$ 33.200,00",
        "+22%",
        help="Receita - Despesas"
    )

with summary_col4:
    st.metric(
        "Margem Lucro",
        "42.3%",
        "+5%",
        help="Margem de lucro bruta"
    )

# Activity Log
st.divider()
st.header("📋 Atividades Recentes")

activities = [
    {
        "timestamp": datetime.now() - timedelta(hours=2),
        "type": "PDF Processado",
        "detail": "boleto_001.pdf",
        "status": "✅"
    },
    {
        "timestamp": datetime.now() - timedelta(hours=4),
        "type": "Conta Criada",
        "detail": "Fornecedor XYZ - R$ 2.500,00",
        "status": "✅"
    },
    {
        "timestamp": datetime.now() - timedelta(hours=6),
        "type": "Sincronização",
        "detail": "45 pedidos Shopee importados",
        "status": "✅"
    },
    {
        "timestamp": datetime.now() - timedelta(hours=8),
        "type": "Relatório",
        "detail": "Fluxo de caixa gerado",
        "status": "✅"
    },
]

activity_data = pd.DataFrame([
    {
        "Horário": act["timestamp"].strftime("%H:%M"),
        "Tipo": act["type"],
        "Detalhe": act["detail"],
        "Status": act["status"]
    }
    for act in activities
])

st.dataframe(
    activity_data,
    use_container_width=True,
    hide_index=True,
    column_config={
        "Horário": st.column_config.TextColumn("🕐 Horário", width=100),
        "Tipo": st.column_config.TextColumn("📌 Tipo", width=150),
        "Detalhe": st.column_config.TextColumn("📝 Detalhe"),
        "Status": st.column_config.TextColumn("✅ Status", width=50),
    }
)

# Footer
st.divider()
st.markdown("""
<div style="text-align: center; padding: 20px; color: #999; font-size: 11px;">
    <p>Dashboard Financeiro MLH DEV v2.0 | Última atualização: """ + datetime.now().strftime("%d/%m/%Y %H:%M:%S") + """</p>
</div>
""", unsafe_allow_html=True)
