import streamlit as st
from dashboard.visualizacao_contas import visualizar_contas_a_pagar

def main():
    st.sidebar.title("Menu")
    opcoes = ["Contas a Pagar", "Outras Funcionalidades"]
    escolha = st.sidebar.selectbox("Escolha uma opção", opcoes)

    if escolha == "Contas a Pagar":
        visualizar_contas_a_pagar()
    elif escolha == "Outras Funcionalidades":
        st.write("Em desenvolvimento...")

if __name__ == "__main__":
    main()
