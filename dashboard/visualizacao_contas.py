import plotly.express as px
import streamlit as st
import pandas as pd
from api.contas_pagar import listar_contas

def visualizar_contas_a_pagar():
    """
    Visualiza as contas a pagar em um dashboard usando Streamlit.
    """
    st.title("Contas a Pagar")
    st.write("Visualização das contas a pagar")

    contas = listar_contas()
    df_contas = pd.DataFrame(contas)

    st.dataframe(df_contas)

    # Indicadores principais
    st.subheader("Indicadores Principais")
    total_pagar = df_contas['valor'].sum()
    total_pagas = df_contas[df_contas['status'] == 'paga']['valor'].sum()
    total_pendentes = total_pagar - total_pagas

    st.metric(label="Total a Pagar", value=f"R$ {total_pagar:.2f}")
    st.metric(label="Total Pagas", value=f"R$ {total_pagas:.2f}")
    st.metric(label="Total Pendentes", value=f"R$ {total_pendentes:.2f}")
    st.subheader("Gráficos de Receitas/Despesas")
    if not df_contas.empty:
        fig = px.bar(df_contas, x='data_vencimento', y='valor', color='status', title="Receitas/Despesas ao longo do tempo")
        st.plotly_chart(fig)
    else:
        st.write("Nenhuma conta disponível para exibir gráficos.")

if __name__ == "__main__":
    visualizar_contas_a_pagar()
