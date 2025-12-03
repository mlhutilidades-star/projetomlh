"""
Bulk import from CSV or Apps Script export
"""
import streamlit as st
import pandas as pd
from datetime import datetime
from modules.database import get_db, ContaPagar, add_or_update_regra
from modules.validation import normalize_cnpj, parse_valor, parse_date_br
import logging

logger = logging.getLogger('import')

st.set_page_config(page_title="Importação", page_icon="📥", layout="wide")
st.title("📥 Importação em Lote")

st.markdown("""
### Como usar:
1. **Baixe o template** ou use exportação de outro sistema
2. **Preencha os dados** no Excel/CSV
3. **Faça upload** e revise
4. **Confirme** a importação

**Formatos aceitos:** CSV, Excel (.xlsx, .xls)
""")

# Template download
st.subheader("1️⃣ Template para Importação")
col1, col2 = st.columns(2)

with col1:
    template_data = {
        'vencimento': ['31/12/2025', '15/01/2026'],
        'fornecedor': ['Exemplo LTDA', 'Fornecedor Teste'],
        'cnpj': ['12.345.678/0001-99', '98.765.432/0001-10'],
        'categoria': ['Fornecedores', 'Energia'],
        'descricao': ['Descrição opcional', 'Nota fiscal 12345'],
        'valor': ['1500.00', '2500.50'],
        'status': ['Pendente', 'Pago'],
        'linha_digitavel': ['', '12345.67890 12345.678901...'],
        'observacoes': ['', 'Pagamento via PIX']
    }
    
    df_template = pd.DataFrame(template_data)
    csv_template = df_template.to_csv(index=False, encoding='utf-8-sig')
    
    st.download_button(
        label="📄 Baixar Template CSV",
        data=csv_template,
        file_name="template_importacao_contas.csv",
        mime="text/csv",
        use_container_width=True
    )

with col2:
    st.info("""
    **Campos obrigatórios:**
    - vencimento (DD/MM/AAAA)
    - fornecedor
    - valor
    
    **Campos opcionais:**
    - cnpj, categoria, descricao, status, linha_digitavel, observacoes
    """)

# File upload
st.markdown("---")
st.subheader("2️⃣ Upload do Arquivo")

uploaded_file = st.file_uploader(
    "Arraste o arquivo aqui ou clique para selecionar",
    type=['csv', 'xlsx', 'xls'],
    help="Formatos: CSV (UTF-8), Excel"
)

if uploaded_file:
    try:
        # Read file
        if uploaded_file.name.endswith('.csv'):
            df = pd.read_csv(uploaded_file, encoding='utf-8-sig')
        else:
            df = pd.read_excel(uploaded_file)
        
        st.success(f"✅ Arquivo lido com sucesso: {len(df)} linha(s)")
        
        # Preview
        st.subheader("3️⃣ Pré-visualização dos Dados")
        st.dataframe(df.head(20), use_container_width=True)
        
        # Validation
        required_cols = ['vencimento', 'fornecedor', 'valor']
        missing_cols = [col for col in required_cols if col not in df.columns]
        
        if missing_cols:
            st.error(f"❌ Colunas obrigatórias faltando: {', '.join(missing_cols)}")
            st.stop()
        
        # Statistics
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("📊 Total de Linhas", len(df))
        with col2:
            total_valor = df['valor'].apply(lambda x: parse_valor(str(x)) if pd.notna(x) else 0).sum()
            st.metric("💰 Valor Total", f"R$ {total_valor:,.2f}")
        with col3:
            valid_cnpj = df['cnpj'].notna().sum() if 'cnpj' in df.columns else 0
            st.metric("🏢 CNPJs Informados", valid_cnpj)
        
        # Import button
        st.markdown("---")
        st.subheader("4️⃣ Confirmar Importação")
        
        col1, col2 = st.columns([3, 1])
        with col1:
            create_rules = st.checkbox(
                "✅ Criar/atualizar regras automaticamente para CNPJs válidos",
                value=True,
                help="Incrementa contador de uso das regras M11"
            )
        
        with col2:
            if st.button("🚀 IMPORTAR", type="primary", use_container_width=True):
                db = get_db()
                success_count = 0
                error_count = 0
                errors_list = []
                
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                for idx, row in df.iterrows():
                    try:
                        status_text.text(f"Processando {idx+1}/{len(df)}...")
                        progress_bar.progress((idx + 1) / len(df))
                        
                        # Parse data
                        vencimento_parsed = parse_date_br(str(row['vencimento']))
                        if not vencimento_parsed:
                            raise ValueError(f"Data inválida: {row['vencimento']}")
                        
                        valor_parsed = parse_valor(str(row['valor']))
                        if valor_parsed <= 0:
                            raise ValueError(f"Valor inválido: {row['valor']}")
                        
                        cnpj_val = normalize_cnpj(str(row['cnpj'])) if pd.notna(row.get('cnpj')) else None
                        
                        # Create conta
                        nova_conta = ContaPagar(
                            mes=vencimento_parsed.month,
                            vencimento=vencimento_parsed.date(),
                            fornecedor=str(row['fornecedor']).strip(),
                            cnpj=cnpj_val,
                            categoria=str(row['categoria']).strip() if pd.notna(row.get('categoria')) else None,
                            descricao=str(row['descricao']).strip() if pd.notna(row.get('descricao')) else None,
                            valor=valor_parsed,
                            status=str(row.get('status', 'Pendente')).strip(),
                            linha_digitavel=str(row['linha_digitavel']).strip() if pd.notna(row.get('linha_digitavel')) else None,
                            observacoes=str(row['observacoes']).strip() if pd.notna(row.get('observacoes')) else None
                        )
                        
                        db.add(nova_conta)
                        
                        # Create/update rule
                        if create_rules and cnpj_val and nova_conta.fornecedor and nova_conta.categoria:
                            add_or_update_regra(cnpj_val, nova_conta.fornecedor, nova_conta.categoria)
                        
                        success_count += 1
                        
                    except Exception as e:
                        error_count += 1
                        errors_list.append(f"Linha {idx+1}: {str(e)[:100]}")
                        logger.error(f"Erro na linha {idx+1}: {e}", exc_info=True)
                
                db.commit()
                db.close()
                
                progress_bar.empty()
                status_text.empty()
                
                # Results
                st.success(f"✅ Importação concluída: {success_count} conta(s) importada(s)")
                
                if error_count > 0:
                    st.warning(f"⚠️ {error_count} erro(s) encontrado(s)")
                    with st.expander("Ver erros"):
                        for err in errors_list[:50]:  # Show first 50
                            st.text(err)
                
                st.balloons()
                
    except Exception as e:
        st.error(f"❌ Erro ao processar arquivo: {e}")
        logger.error(f"Erro no upload: {e}", exc_info=True)

else:
    st.info("👆 Faça upload de um arquivo para começar a importação")

# Tips
st.markdown("---")
st.markdown("""
### 💡 Dicas:
- Use o **template** para garantir formato correto
- **Verifique os dados** na pré-visualização antes de importar
- O sistema **normaliza CNPJs** automaticamente
- **Regras M11** são criadas/atualizadas se opção ativada
- Em caso de erro, revise a linha indicada no arquivo
""")
