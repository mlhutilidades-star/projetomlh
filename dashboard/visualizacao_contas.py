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

if __name__ == "__main__":
    visualizar_contas_a_pagar()
