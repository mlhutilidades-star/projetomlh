# app.py
import streamlit as st
from dotenv import load_dotenv

load_dotenv()
st.set_page_config(layout="wide", page_title="HUB Financeiro - MLH DEV")
st.title("HUB Financeiro – MLH DEV")

tab1, tab2, tab3, tab4 = st.tabs(["Visão Geral", "Tiny ERP", "Shopee", "Processador de PDF"])

with tab1:
    st.header("Visão Geral")
    st.write("Dashboard com KPIs consolidados. (Em construção...)")

with tab2:
    st.header("Módulo Tiny ERP")
    st.write("Interação com dados do Tiny. (Em construção...)")

with tab3:
    st.header("Módulo Shopee")
    st.write("Dados de pedidos, produtos e taxas. (Em construção...)")

with tab4:
    st.header("Processador de Boletos PDF")
    uploaded_file = st.file_uploader("Escolha um arquivo PDF", type="pdf")
    if uploaded_file is not None:
        st.success("Arquivo recebido! Lógica de processamento a ser implementada.")
        with open(log_file, 'r', encoding='utf-8') as f:
            recent_logs = f.readlines()[-50:]  # últimas 50 linhas
        with st.sidebar.expander('📋 Recent Logs'):
            st.text(''.join(recent_logs))
