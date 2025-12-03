"""Gerenciar Regras de Custo por Fornecedor

Interface para criar, editar e ativar/desativar regras customizadas de
cálculo de custo por fornecedor a partir de NF-e.
"""
import streamlit as st
import pandas as pd
from modules.database import (
    list_regras_custo,
    add_or_update_regra_custo,
    delete_regra_custo,
    get_regra_custo,
    init_database
)

st.set_page_config(page_title="Regras de Custo", page_icon="🧮", layout="wide")

st.title("🧮 Regras de Custo por Fornecedor")
st.caption("Defina fórmulas personalizadas para calcular o custo de produtos de cada fornecedor")

# Inicializar DB
init_database()

# Seção: Adicionar/Editar Regra
with st.expander("➕ Adicionar/Editar Regra de Custo", expanded=False):
    st.markdown("""
    **Variáveis disponíveis na fórmula:**
    - `vUnCom`: valor unitário comercial
    - `quantidade`: quantidade
    - `vProd`: valor total do produto
    - `ipi_total`: IPI total do item
    - `ipi_aliq`: alíquota IPI em % (calculada automaticamente)
    - `st_total`: ICMS ST total
    - `icms_total`: ICMS total
    - `pis_total`: PIS total
    - `cofins_total`: COFINS total
    - `rateio_frete`: frete rateado para o item
    - `rateio_seguro`: seguro rateado para o item
    - `rateio_outros`: outros rateado para o item
    - `rateio_desconto`: desconto rateado para o item
    
    **Exemplo de fórmula:**
    ```
    (vUnCom / 7) + (ipi_aliq * 0.7)
    ```
    """)
    
    col1, col2 = st.columns(2)
    with col1:
        fornecedor_input = st.text_input("Nome do Fornecedor", help="Nome exato do fornecedor (case-insensitive)")
    with col2:
        formula_input = st.text_area("Fórmula de Custo", height=100, help="Use variáveis listadas acima")
    
    col3, col4 = st.columns(2)
    with col3:
        ativo_input = st.checkbox("Ativar regra", value=True)
    with col4:
        obs_input = st.text_input("Observações (opcional)")
    
    if st.button("💾 Salvar Regra"):
        if fornecedor_input and formula_input:
            try:
                add_or_update_regra_custo(
                    fornecedor=fornecedor_input,
                    formula=formula_input,
                    ativo=ativo_input,
                    observacoes=obs_input
                )
                st.success(f"✅ Regra salva para '{fornecedor_input}'")
                st.rerun()
            except Exception as e:
                st.error(f"Erro ao salvar regra: {e}")
        else:
            st.warning("Preencha fornecedor e fórmula")

# Seção: Listar Regras
st.markdown("---")
st.subheader("📋 Regras Cadastradas")

filtro = st.radio("Filtrar", ["Todas", "Apenas Ativas", "Apenas Inativas"], horizontal=True)

if filtro == "Apenas Ativas":
    regras = list_regras_custo(apenas_ativas=True)
elif filtro == "Apenas Inativas":
    todas = list_regras_custo(apenas_ativas=False)
    regras = [r for r in todas if not r['ativo']]
else:
    regras = list_regras_custo(apenas_ativas=False)

if not regras:
    st.info("Nenhuma regra cadastrada ainda. Use o formulário acima para adicionar.")
else:
    df = pd.DataFrame(regras)
    df['ativo'] = df['ativo'].apply(lambda x: '✅' if x else '❌')
    df['ultima_atualizacao'] = pd.to_datetime(df['ultima_atualizacao']).dt.strftime('%d/%m/%Y %H:%M')
    
    st.dataframe(
        df[['fornecedor', 'formula', 'ativo', 'contador_usos', 'ultima_atualizacao', 'observacoes']],
        use_container_width=True,
        hide_index=True
    )
    
    # Ações
    st.markdown("### ⚙️ Ações")
    col_a, col_b = st.columns(2)
    
    with col_a:
        st.markdown("**Editar Regra**")
        forn_edit = st.selectbox("Selecione fornecedor", [r['fornecedor'] for r in regras], key="edit_sel")
        if st.button("📝 Carregar para Edição"):
            regra_edit = get_regra_custo(forn_edit)
            if regra_edit:
                st.session_state['edit_fornecedor'] = regra_edit['fornecedor']
                st.session_state['edit_formula'] = regra_edit['formula']
                st.session_state['edit_ativo'] = regra_edit['ativo']
                st.session_state['edit_obs'] = regra_edit['observacoes'] or ''
                st.info(f"Regra de '{forn_edit}' carregada. Role para cima e edite no formulário.")
    
    with col_b:
        st.markdown("**Excluir Regra**")
        forn_del = st.selectbox("Selecione fornecedor", [r['fornecedor'] for r in regras], key="del_sel")
        if st.button("🗑️ Excluir Regra", type="secondary"):
            if delete_regra_custo(forn_del):
                st.success(f"✅ Regra de '{forn_del}' excluída")
                st.rerun()
            else:
                st.error("Erro ao excluir regra")

# Pré-preencher formulário se editando
if 'edit_fornecedor' in st.session_state:
    fornecedor_input = st.session_state.pop('edit_fornecedor')
    formula_input = st.session_state.pop('edit_formula')
    ativo_input = st.session_state.pop('edit_ativo')
    obs_input = st.session_state.pop('edit_obs')
