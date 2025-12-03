"""
Gestão de Contas a Pagar
"""

import streamlit as st
import pandas as pd
from datetime import datetime
from modules.database import get_db, ContaPagar, get_regra, add_or_update_regra, RegraM11
from modules.export_utils import export_to_excel, get_export_filename
from modules.validation import normalize_cnpj, detect_duplicate_conta

st.set_page_config(page_title="Contas a Pagar", page_icon="💳", layout="wide")

st.title("💳 Contas a Pagar")

# Tabs
tab1, tab2 = st.tabs(["📋 Lista de Contas", "➕ Nova Conta"])

# TAB 1: Lista de contas
with tab1:
    st.subheader("📋 Todas as Contas")
    
    # Filtros
    col1, col2, col3 = st.columns(3)
    
    with col1:
        filtro_mes = st.selectbox(
            "Filtrar por mês",
            ["Todos"] + [f"{i:02d} - {m}" for i, m in enumerate([
                "JAN", "FEV", "MAR", "ABR", "MAI", "JUN",
                "JUL", "AGO", "SET", "OUT", "NOV", "DEZ"
            ], 1)]
        )
    
    with col2:
        filtro_status = st.selectbox(
            "Filtrar por status",
            ["Todos", "Pendente", "Pago", "Cancelado"]
        )
    
    with col3:
        filtro_categoria = st.text_input("Buscar categoria/fornecedor")
    
    # Buscar contas
    db = get_db()
    query = db.query(ContaPagar)
    
    if filtro_mes != "Todos":
        mes_num = int(filtro_mes.split(" ")[0])
        query = query.filter(ContaPagar.mes == mes_num)
    
    if filtro_status != "Todos":
        query = query.filter(ContaPagar.status == filtro_status)
    
    if filtro_categoria:
        query = query.filter(
            (ContaPagar.categoria.like(f"%{filtro_categoria}%")) |
            (ContaPagar.fornecedor.like(f"%{filtro_categoria}%"))
        )
    
    contas = query.order_by(ContaPagar.vencimento.desc()).all()
    
    if contas:
        df = pd.DataFrame([{
            'ID': c.id,
            'Mês': f"M{c.mes}",
            'Vencimento': c.vencimento.strftime('%d/%m/%Y'),
            'Fornecedor': c.fornecedor,
            'CNPJ': c.cnpj or '-',
            'Categoria': c.categoria or '-',
            'Valor': c.valor,
            'Status': c.status
        } for c in contas])
        
        # Formatar valor como moeda
        df['Valor'] = df['Valor'].apply(lambda x: f"R$ {x:,.2f}")
        
        st.dataframe(df, use_container_width=True, hide_index=True)
        
        # Estatísticas
        col1, col2, col3 = st.columns(3)
        with col1:
            total = sum(c.valor for c in contas)
            st.metric("💰 Valor Total", f"R$ {total:,.2f}")
        with col2:
            st.metric("📊 Total de Contas", len(contas))
        with col3:
            # Export button
            if st.button("📥 Exportar para Excel", use_container_width=True):
                db_export = get_db()
                all_contas = db_export.query(ContaPagar).all()
                all_regras = db_export.query(RegraM11).all()
                db_export.close()
                
                excel_file = export_to_excel(all_contas, all_regras)
                filename = get_export_filename('hub_financeiro')
                
                st.download_button(
                    label="⬇️ Baixar Excel",
                    data=excel_file,
                    file_name=f"{filename}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True
                )
    else:
        st.info("Nenhuma conta encontrada com os filtros selecionados")
    
    db.close()

# TAB 2: Nova conta
with tab2:
    st.subheader("➕ Cadastrar Nova Conta")

    # Prefill por CNPJ (fora do form para reatividade)
    st.markdown("### 🔎 Prefill por CNPJ")
    prefill_cnpj = st.text_input("CNPJ para buscar regra", key="prefill_cnpj", placeholder="00.000.000/0000-00")

    # Upload de boleto PDF inline (opcional) para extrair dados e preencher automaticamente
    st.markdown("### 📄 Anexar Boleto (PDF)")
    boleto_file = st.file_uploader("Envie o PDF do boleto para tentar extrair dados", type=['pdf'])
    if boleto_file:
        from modules.pdf_parser import extract_from_pdf, ocr_status
        pdf_bytes = boleto_file.read()
        dados_pdf = extract_from_pdf(pdf_bytes, filename=boleto_file.name)
        st.caption(f"Status OCR: {ocr_status()}")
        with st.expander("Dados extraídos do PDF"):
            st.json(dados_pdf)
        # Ajustar prefill se vierem dados
        if dados_pdf.get('cnpj'):
            prefill_cnpj = dados_pdf.get('cnpj')
            st.session_state['prefill_cnpj'] = prefill_cnpj
        # Guardar valores para uso no formulário
        st.session_state['pdf_prefill_fornecedor'] = st.session_state.get('prefill_fornecedor','')  # pode ser atualizado por regra depois
        st.session_state['pdf_prefill_categoria'] = st.session_state.get('prefill_categoria','')
        st.session_state['pdf_prefill_valor'] = dados_pdf.get('valor','')
        st.session_state['pdf_prefill_vencimento'] = dados_pdf.get('vencimento','')
        st.session_state['pdf_prefill_linha'] = dados_pdf.get('linha_digitavel','')
        st.session_state['pdf_nome_arquivo'] = boleto_file.name

    if prefill_cnpj:
        regra = get_regra(prefill_cnpj)
        if regra and regra.get('ativo'):
            st.success(f"Regra ativa encontrada: Fornecedor: **{regra['fornecedor']}**, Categoria: **{regra['categoria']}** (usos: {regra['contador_usos']})")
            st.session_state['prefill_fornecedor'] = regra['fornecedor']
            st.session_state['prefill_categoria'] = regra['categoria']
        else:
            st.info("Nenhuma regra ativa para este CNPJ ainda. Será criada após usos suficientes.")
    else:
        st.session_state.setdefault('prefill_fornecedor', '')
        st.session_state.setdefault('prefill_categoria', '')

    categorias_lista = [
        "", "Aluguel", "Energia", "Água", "Internet",
        "Telefone", "Fornecedores", "Salários", "Impostos",
        "Marketing", "Outros"
    ]

    # Formulário principal
    with st.form("form_nova_conta"):
        col1, col2 = st.columns(2)
        with col1:
            # Se veio vencimento do PDF tentar parse
            pdf_venc_str = st.session_state.get('pdf_prefill_vencimento','')
            default_venc = datetime.now()
            if pdf_venc_str:
                try:
                    default_venc = datetime.strptime(pdf_venc_str, '%d/%m/%Y')
                except Exception:
                    pass
            vencimento = st.date_input("Data de Vencimento *", default_venc)
            fornecedor = st.text_input("Fornecedor *", value=st.session_state.get('prefill_fornecedor',''))
            cnpj = st.text_input("CNPJ", placeholder="00.000.000/0000-00", value=prefill_cnpj)
            # Categoria: se prefill disponível, selecionar índice correspondente
            categoria_default = st.session_state.get('prefill_categoria','')
            if categoria_default in categorias_lista:
                categoria_index = categorias_lista.index(categoria_default)
            else:
                categoria_index = 0
            categoria = st.selectbox("Categoria", categorias_lista, index=categoria_index)
        with col2:
            valor_prefill = 0.00
            valor_str_pdf = st.session_state.get('pdf_prefill_valor','')
            if valor_str_pdf:
                try:
                    valor_prefill = float(valor_str_pdf)
                except Exception:
                    valor_prefill = 0.00
            valor = st.number_input("Valor *", min_value=0.01, step=0.01, format="%.2f", value=valor_prefill if valor_prefill>0 else 0.01)
            status = st.selectbox("Status", ["Pendente", "Pago", "Cancelado"])
            linha_digitavel = st.text_input("Linha Digitável", value=st.session_state.get('pdf_prefill_linha',''))
            pdf_url = st.text_input("Nome do Arquivo PDF", value=st.session_state.get('pdf_nome_arquivo',''))
        descricao = st.text_area("Descrição")
        observacoes = st.text_area("Observações")
        submitted = st.form_submit_button("💾 Salvar Conta", use_container_width=True)

        if submitted:
            if not fornecedor or not vencimento or valor <= 0:
                st.error("❌ Preencha os campos obrigatórios: Vencimento, Fornecedor e Valor")
            else:
                db = get_db()
                try:
                    # Normalize CNPJ
                    cnpj_normalizado = normalize_cnpj(cnpj) if cnpj else None
                    
                    # Check for duplicates
                    duplicata = detect_duplicate_conta(db, fornecedor, valor, vencimento)
                    if duplicata:
                        st.warning(f"⚠️ Possível duplicata encontrada: Conta #{duplicata.id} - {duplicata.fornecedor} - R$ {duplicata.valor:.2f} em {duplicata.vencimento.strftime('%d/%m/%Y')}")
                        if not st.checkbox("✅ Confirmar cadastro mesmo assim"):
                            st.stop()
                    
                    nova_conta = ContaPagar(
                        mes=vencimento.month,
                        vencimento=vencimento,
                        fornecedor=fornecedor,
                        cnpj=cnpj_normalizado,
                        categoria=categoria if categoria else None,
                        descricao=descricao if descricao else None,
                        valor=valor,
                        status=status,
                        linha_digitavel=linha_digitavel if linha_digitavel else None,
                        pdf_url=pdf_url if pdf_url else None,
                        observacoes=observacoes if observacoes else None
                    )
                    db.add(nova_conta)
                    db.commit()

                    # Atualiza / cria regra se CNPJ fornecido
                    if cnpj and fornecedor and categoria:
                        regra_criada = add_or_update_regra(cnpj, fornecedor, categoria)
                        if regra_criada and regra_criada.ativo:
                            st.success(f"🔁 Regra ativada para {cnpj}: {fornecedor} / {categoria}")
                        else:
                            st.info("Regra registrada / atualizada. Será ativada após atingir 3 usos.")

                    st.success(f"✅ Conta #{nova_conta.id} cadastrada com sucesso!")
                    st.balloons()
                finally:
                    db.close()
