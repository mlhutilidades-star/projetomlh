"""
Gestão de Regras (Aprendizado por CNPJ)
"""
import streamlit as st
from modules.database import get_db, RegraM11

st.set_page_config(page_title="Regras M11", page_icon="🧠", layout="wide")
st.title("🧠 Regras de Aprendizado (M11)")

st.caption("Regras são ativadas automaticamente após 3 usos do mesmo CNPJ.")

# Carregar regras
with st.spinner("Carregando regras..."):
    db = get_db()
    regras = db.query(RegraM11).order_by(RegraM11.contador_usos.desc()).all()
    db.close()

if not regras:
    st.info("Nenhuma regra cadastrada ainda. Cadastre contas com CNPJ para iniciar aprendizado.")
else:
    # Preparar DataFrame
    import pandas as pd
    df = pd.DataFrame([
        {
            'ID': r.id,
            'CNPJ': r.cnpj,
            'Fornecedor': r.fornecedor,
            'Categoria': r.categoria,
            'Usos': r.contador_usos,
            'Ativo': r.ativo,
        } for r in regras
    ])

    st.subheader("📋 Lista de Regras")
    edited_df = st.data_editor(
        df,
        use_container_width=True,
        hide_index=True,
        key="editor_regras",
        num_rows="dynamic",
        column_config={
            'Ativo': st.column_config.CheckboxColumn(help="Marcar para ativar/desativar manualmente"),
            'Usos': st.column_config.NumberColumn(disabled=True),
            'ID': st.column_config.NumberColumn(disabled=True)
        }
    )

    if st.button("💾 Salvar Alterações", use_container_width=True):
        db = get_db()
        try:
            for _, row in edited_df.iterrows():
                regra = db.query(RegraM11).filter(RegraM11.id == int(row['ID'])).first()
                if not regra:
                    continue
                # Atualizações permitidas
                regra.fornecedor = row['Fornecedor'] or regra.fornecedor
                regra.categoria = row['Categoria'] or regra.categoria
                regra.ativo = bool(row['Ativo']) if regra.contador_usos >= 3 else regra.ativo  # só permite ativar manual se já tem usos suficientes
            db.commit()
            st.success("✅ Regras atualizadas com sucesso!")
        finally:
            db.close()

    # Métricas
    col1, col2, col3 = st.columns(3)
    total_regras = len(regras)
    regras_ativas = sum(1 for r in regras if r.ativo)
    proximas_ativas = sum(1 for r in regras if not r.ativo and r.contador_usos >= 2)
    with col1:
        st.metric("Total de Regras", total_regras)
    with col2:
        st.metric("Regras Ativas", regras_ativas)
    with col3:
        st.metric("Próximas a Ativar (>=2 usos)", proximas_ativas)

st.markdown("---")
st.markdown("### ℹ️ Como funciona")
st.markdown("""
1. Cada vez que uma conta com CNPJ é cadastrada, o sistema registra/atualiza a regra.
2. Após atingir **3 usos**, a regra torna-se **ativa** e passa a preencher automaticamente Fornecedor e Categoria.
3. Você pode ajustar manualmente os campos. A ativação manual só é permitida se já houver uso suficiente (>=3).
""")
