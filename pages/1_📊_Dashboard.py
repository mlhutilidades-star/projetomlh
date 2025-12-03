"""
Dashboard - Visão Geral
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta, date
from modules.database import get_db, ContaPagar
from modules.analytics import kpis_global, categorias_sum, top_fornecedores, monthly_series, shopee_stats, cogs_fill_rate
from modules.cache import clear_cache, invalidate_cache
from sqlalchemy import func

st.set_page_config(page_title="Dashboard", page_icon="📊", layout="wide")

st.title("📊 Dashboard - Visão Geral")
st.caption("Visão consolidada com receita vs despesas, tendências e destaques")

# Sidebar: Filtros
with st.sidebar:
    st.header("🔍 Filtros")
    
    # Filtro de período
    periodo_opcao = st.selectbox(
        "Período",
        ["Últimos 7 dias", "Últimos 30 dias", "Últimos 90 dias", "Último ano", "Personalizado"],
        index=2
    )
    
    hoje = date.today()
    if periodo_opcao == "Últimos 7 dias":
        data_inicio = hoje - timedelta(days=7)
        data_fim = hoje
    elif periodo_opcao == "Últimos 30 dias":
        data_inicio = hoje - timedelta(days=30)
        data_fim = hoje
    elif periodo_opcao == "Últimos 90 dias":
        data_inicio = hoje - timedelta(days=90)
        data_fim = hoje
    elif periodo_opcao == "Último ano":
        data_inicio = hoje - timedelta(days=365)
        data_fim = hoje
    else:  # Personalizado
        col_a, col_b = st.columns(2)
        with col_a:
            data_inicio = st.date_input("De", value=hoje - timedelta(days=90))
        with col_b:
            data_fim = st.date_input("Até", value=hoje)
    
    # Filtro de categoria
    db = get_db()
    categorias_disponiveis = db.query(ContaPagar.categoria).distinct().all()
    categorias_list = ["Todas"] + sorted([c[0] for c in categorias_disponiveis if c[0]])
    categoria_filtro = st.selectbox("Categoria", categorias_list)
    
    # Filtro de status
    status_filtro = st.selectbox("Status", ["Todos", "Pendente", "Pago"])
    
    # Botão para limpar cache
    if st.button("🔄 Atualizar Dados"):
        clear_cache()
        st.success("Cache limpo! Dados atualizados.")
        st.rerun()

# KPIs principais com filtros aplicados
kpis = kpis_global(db, data_inicio=data_inicio, data_fim=data_fim)

col1, col2, col3, col4 = st.columns(4)

# Total de contas (sem filtro de período para total geral)
total_contas = db.query(func.count(ContaPagar.id)).scalar() or 0

# Contas pendentes
contas_pendentes = kpis['pendentes']

# Valor total pendente
valor_pendente = kpis['valor_pendente']

# Contas vencidas
contas_vencidas = kpis['vencidas']

with col1:
    st.metric("📋 Total de Contas", total_contas)

with col2:
    st.metric("⏳ Pendentes", contas_pendentes)

with col3:
    st.metric("💰 Valor Pendente", f"R$ {valor_pendente:,.2f}")

with col4:
    st.metric("⚠️ Vencidas", contas_vencidas, delta_color="inverse")

st.markdown("---")

# Composição Receita x COGS x Margem
fill = cogs_fill_rate(db, data_inicio=data_inicio, data_fim=data_fim)
comp_cols = st.columns([2,1])
with comp_cols[0]:
    comp_df = pd.DataFrame({
        'Categoria': ['Receita', 'COGS', 'Margem Contribuição'],
        'Valor': [
            kpis['receitas_periodo'],
            kpis['cogs_periodo'],
            kpis['margem_contrib_valor']
        ]
    })
    fig_comp = px.bar(comp_df, x='Categoria', y='Valor', color='Categoria',
                      color_discrete_map={'Receita':'#2ECC71','COGS':'#F1C40F','Margem Contribuição':'#3498DB'})
    fig_comp.update_layout(yaxis_title='Valor (R$)', height=340)
    st.plotly_chart(fig_comp, use_container_width=True)
with comp_cols[1]:
    st.subheader("Qualidade COGS")
    st.metric("Pedidos com Receita", fill['pedidos_receita'])
    st.metric("Pedidos com COGS", fill['pedidos_cogs'])
    st.metric("Fill Rate COGS", f"{fill['fill_rate_percent']:.1f}%")
    if fill['fill_rate_percent'] < 70:
        st.warning("Muitos pedidos sem custo do produto. Verifique SKUs no Tiny.")
    elif fill['fill_rate_percent'] < 90:
        st.info("Há melhoria possível na cobertura de custos.")
    else:
        st.success("Boa cobertura de custos dos pedidos.")

# KPIs avançados com período filtrado
colA, colB, colC, colD = st.columns(4)
with colA:
    st.metric(f"🟢 Receita ({periodo_opcao})", f"R$ {kpis['receitas_periodo']:,.2f}")
with colB:
    st.metric(f"🧾 Custo Produto (COGS)", f"R$ {kpis['cogs_periodo']:,.2f}")
with colC:
    st.metric(f"🔴 Outras Despesas", f"R$ {kpis['despesas_periodo']:,.2f}")
with colD:
    st.metric(
        f"🏭 Margem Contrib ({periodo_opcao})",
        f"R$ {kpis['margem_contrib_valor']:,.2f}",
        f"{kpis['margem_contrib_percent']:,.1f}%"
    )

st.caption("Margem de contribuição = Receita - Custo do Produto (Tiny). Outras despesas exibidas separadamente.")

# Gráficos
col1, col2 = st.columns(2)

with col1:
    st.subheader("📊 Contas por Status")
    
    # Dados por status com filtros
    query_status = db.query(
        ContaPagar.status,
        func.count(ContaPagar.id).label('quantidade')
    ).filter(ContaPagar.vencimento.between(data_inicio, data_fim))
    
    if categoria_filtro != "Todas":
        query_status = query_status.filter(ContaPagar.categoria == categoria_filtro)
    
    status_data = query_status.group_by(ContaPagar.status).all()
    
    if status_data:
        df_status = pd.DataFrame(status_data, columns=['Status', 'Quantidade'])
        fig_status = px.pie(
            df_status,
            values='Quantidade',
            names='Status',
            hole=0.4,
            color_discrete_sequence=['#FF6B6B', '#4ECDC4', '#95E1D3']
        )
        st.plotly_chart(fig_status, use_container_width=True)
    else:
        st.info("Nenhuma conta cadastrada ainda")

with col2:
    st.subheader("💵 Contas por Categoria")
    cats = categorias_sum(db, data_inicio=data_inicio, data_fim=data_fim)
    if cats:
        df_categoria = pd.DataFrame(cats, columns=['Categoria', 'Valor'])
        # Aplica filtro adicional se necessário
        if categoria_filtro != "Todas":
            df_categoria = df_categoria[df_categoria['Categoria'] == categoria_filtro]
        
        if not df_categoria.empty:
            fig_categoria = px.bar(
                df_categoria,
                x='Categoria',
                y='Valor',
                color='Valor',
                color_continuous_scale='Viridis'
            )
            st.plotly_chart(fig_categoria, use_container_width=True)
        else:
            st.info("Nenhuma categoria no período selecionado")
    else:
        st.info("Nenhuma conta com categoria definida")

# Timeline mensal
st.markdown("---")
st.subheader("📈 Tendência Mensal (Receita vs Despesa)")

# Filtro de ano para timeline
ano_atual = date.today().year
ano_timeline = st.selectbox("Ano", range(ano_atual - 2, ano_atual + 2), index=2)

ms = monthly_series(db, ano=ano_timeline)
if ms and ms['mes']:
    nomes = ['JAN','FEV','MAR','ABR','MAI','JUN','JUL','AGO','SET','OUT','NOV','DEZ']
    x = [nomes[m-1] for m in ms['mes']]
    fig_timeline = go.Figure()
    fig_timeline.add_trace(go.Bar(x=x, y=ms['receita'], name='Receita', marker_color='#2ECC71'))
    fig_timeline.add_trace(go.Bar(x=x, y=ms['despesa'], name='Despesa', marker_color='#E74C3C'))
    fig_timeline.update_layout(barmode='stack', yaxis=dict(title='Valor (R$)'), hovermode='x unified', height=420)
    st.plotly_chart(fig_timeline, use_container_width=True)
else:
    st.info("📅 Nenhum dado mensal ainda")

# Alertas importantes
st.markdown("---")
if contas_vencidas > 0:
    st.error(f"⚠️ **ATENÇÃO:** {contas_vencidas} conta(s) vencida(s) e pendente(s)!")

if contas_pendentes > 10:
    st.warning(f"📄 Você tem {contas_pendentes} contas pendentes. Considere organizar os pagamentos.")

# Destaques Shopee e próximos vencimentos
st.markdown("---")
sh = shopee_stats(db, days=90)
colS1, colS2 = st.columns(2)
with colS1:
    st.subheader("🛍️ Shopee (últimos 90 dias)")
    st.metric("Pedidos importados", sh['count'])
    st.metric("Receita Shopee", f"R$ {sh['total']:,.2f}")
with colS2:
    st.subheader("🏷️ Top 5 Fornecedores")
    tops = top_fornecedores(db, limit=5, data_inicio=data_inicio, data_fim=data_fim)
    if tops:
        df_tops = pd.DataFrame(tops, columns=['Fornecedor','Valor'])
        df_tops['Valor'] = df_tops['Valor'].apply(lambda x: f"R$ {x:,.2f}")
        st.dataframe(df_tops, use_container_width=True, hide_index=True)
    else:
        st.info("Sem fornecedores cadastrados")

st.subheader("📅 Próximos Vencimentos (7 dias)")

proximos_7dias = hoje + timedelta(days=7)
query_proximas = db.query(ContaPagar).filter(
    ContaPagar.vencimento.between(hoje, proximos_7dias),
    ContaPagar.status == "Pendente"
)

if categoria_filtro != "Todas":
    query_proximas = query_proximas.filter(ContaPagar.categoria == categoria_filtro)

contas_proximas = query_proximas.order_by(ContaPagar.vencimento).all()

if contas_proximas:
    df_proximas = pd.DataFrame([{
        'ID': c.id,
        'Vencimento': c.vencimento.strftime('%d/%m/%Y'),
        'Fornecedor': c.fornecedor,
        'Categoria': c.categoria or '-',
        'Valor': f"R$ {c.valor:,.2f}",
        'Status': c.status
    } for c in contas_proximas])
    
    st.dataframe(df_proximas, use_container_width=True, hide_index=True)
else:
    st.success("✅ Nenhuma conta vencendo nos próximos 7 dias!")

db.close()
