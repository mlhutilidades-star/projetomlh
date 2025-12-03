"""
Alert system for upcoming payments and overdue accounts
"""
import streamlit as st
from datetime import datetime, timedelta
from modules.database import get_db, ContaPagar
import logging

logger = logging.getLogger('alerts')

st.set_page_config(page_title="Alertas", page_icon="🔔", layout="wide")
st.title("🔔 Alertas e Notificações")

db = get_db()
hoje = datetime.now().date()

# Vencidas
st.subheader("⚠️ Contas Vencidas")
vencidas = db.query(ContaPagar).filter(
    ContaPagar.vencimento < hoje,
    ContaPagar.status == "Pendente"
).order_by(ContaPagar.vencimento).all()

if vencidas:
    st.error(f"**{len(vencidas)} conta(s) vencida(s)!**")
    
    for conta in vencidas:
        dias_atraso = (hoje - conta.vencimento).days
        with st.expander(f"🚨 {conta.fornecedor} - R$ {conta.valor:,.2f} - Venceu há {dias_atraso} dia(s)"):
            col1, col2, col3 = st.columns(3)
            with col1:
                st.write(f"**ID:** {conta.id}")
                st.write(f"**Vencimento:** {conta.vencimento.strftime('%d/%m/%Y')}")
            with col2:
                st.write(f"**Categoria:** {conta.categoria or '-'}")
                st.write(f"**CNPJ:** {conta.cnpj or '-'}")
            with col3:
                st.write(f"**Descrição:** {conta.descricao or '-'}")
                st.write(f"**Linha Digitável:** {conta.linha_digitavel[:30]+'...' if conta.linha_digitavel else '-'}")
else:
    st.success("✅ Nenhuma conta vencida!")

# Vencendo hoje
st.markdown("---")
st.subheader("📅 Vencendo Hoje")
vencendo_hoje = db.query(ContaPagar).filter(
    ContaPagar.vencimento == hoje,
    ContaPagar.status == "Pendente"
).all()

if vencendo_hoje:
    st.warning(f"**{len(vencendo_hoje)} conta(s) vencendo hoje!**")
    
    for conta in vencendo_hoje:
        st.info(f"⏰ **{conta.fornecedor}** - R$ {conta.valor:,.2f} - Categoria: {conta.categoria or '-'}")
else:
    st.info("Nenhuma conta vence hoje")

# Próximos 7 dias
st.markdown("---")
st.subheader("📆 Vencendo nos Próximos 7 Dias")
proximos_7 = hoje + timedelta(days=7)
vencendo_semana = db.query(ContaPagar).filter(
    ContaPagar.vencimento.between(hoje + timedelta(days=1), proximos_7),
    ContaPagar.status == "Pendente"
).order_by(ContaPagar.vencimento).all()

if vencendo_semana:
    st.info(f"📋 {len(vencendo_semana)} conta(s) vencendo na próxima semana")
    
    import pandas as pd
    df = pd.DataFrame([{
        'ID': c.id,
        'Vencimento': c.vencimento.strftime('%d/%m/%Y'),
        'Dias': (c.vencimento - hoje).days,
        'Fornecedor': c.fornecedor,
        'Categoria': c.categoria or '-',
        'Valor': f"R$ {c.valor:,.2f}"
    } for c in vencendo_semana])
    
    st.dataframe(df, use_container_width=True, hide_index=True)
else:
    st.success("✅ Nenhuma conta vencendo nos próximos 7 dias")

# Próximos 30 dias
st.markdown("---")
st.subheader("📊 Vencendo nos Próximos 30 Dias")
proximos_30 = hoje + timedelta(days=30)
vencendo_mes = db.query(ContaPagar).filter(
    ContaPagar.vencimento.between(hoje + timedelta(days=1), proximos_30),
    ContaPagar.status == "Pendente"
).order_by(ContaPagar.vencimento).all()

if vencendo_mes:
    total_mes = sum(c.valor for c in vencendo_mes)
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric("📋 Quantidade", len(vencendo_mes))
    with col2:
        st.metric("💰 Valor Total", f"R$ {total_mes:,.2f}")
    
    # Group by week
    import pandas as pd
    df_mes = pd.DataFrame([{
        'Semana': f"Semana {((c.vencimento - hoje).days // 7) + 1}",
        'Fornecedor': c.fornecedor,
        'Vencimento': c.vencimento.strftime('%d/%m/%Y'),
        'Valor': c.valor
    } for c in vencendo_mes])
    
    # Summary by week
    semanas = df_mes.groupby('Semana').agg({
        'Valor': ['count', 'sum']
    }).reset_index()
    semanas.columns = ['Semana', 'Quantidade', 'Valor Total']
    semanas['Valor Total'] = semanas['Valor Total'].apply(lambda x: f"R$ {x:,.2f}")
    
    st.dataframe(semanas, use_container_width=True, hide_index=True)
    
    with st.expander("Ver detalhes"):
        st.dataframe(df_mes, use_container_width=True, hide_index=True)
else:
    st.info("Nenhuma conta vencendo nos próximos 30 dias")

db.close()

# Configurações de alertas (future feature)
st.markdown("---")
st.subheader("⚙️ Configurações de Alertas")
st.info("""
🔮 **Em desenvolvimento:**
- Email automático para contas vencendo
- Notificações no navegador
- Alertas personalizados por categoria
- Integração com WhatsApp/Telegram
""")

# Summary
st.markdown("---")
total_pendente = len(vencidas) + len(vencendo_hoje) + len(vencendo_semana)
if total_pendente > 0:
    st.warning(f"⚡ **Atenção necessária:** {total_pendente} conta(s) requerem ação urgente (vencidas ou vencendo esta semana)")
else:
    st.success("🎉 Tudo sob controle! Não há alertas urgentes no momento.")
