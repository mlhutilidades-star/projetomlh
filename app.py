"""
Hub Financeiro - Centro de Comando
Aplicação principal Streamlit
"""

import streamlit as st
from modules.database import init_database
from modules.logging_config import setup_logging
import logging
import traceback
import sys

# Setup logging FIRST
try:
    setup_logging()
    logging.info('=== Hub Financeiro iniciando ===')
except Exception as e:
    print(f"ERRO AO INICIAR LOGGING: {e}", file=sys.stderr)
    traceback.print_exc()

# Configuração da página
try:
    st.set_page_config(
        page_title="Hub Financeiro",
        page_icon="💰",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    logging.info('Streamlit page config OK')
except Exception as e:
    logging.error(f'ERRO no set_page_config: {e}')
    st.error(f"Erro ao configurar página: {e}")

# Inicializa banco de dados
try:
    init_database()
    logging.info('Banco de dados inicializado com sucesso')
except Exception as e:
    logging.error(f'ERRO ao inicializar database: {e}')
    logging.error(traceback.format_exc())
    st.error(f"❌ Erro ao inicializar banco: {e}")
    st.stop()

# Página principal
st.title("💰 Hub Financeiro - Centro de Comando")

st.markdown("""
## Bem-vindo ao Hub Financeiro!

Sistema completo de gestão financeira com:
- 📊 Dashboard inteligente
- 💳 Gestão de contas a pagar
- 📄 Upload e OCR de boletos
- 🤖 Aprendizado automático (M11)
- 🛍️ Integração Shopee (Receitas)

### 🚀 Como usar:
1. Use o menu lateral para navegar
2. Comece pelo **Dashboard** para ver visão geral
3. Ou vá direto para **Contas a Pagar** para gerenciar suas contas

---
""")

# Cards informativos
col1, col2, col3 = st.columns(3)

with col1:
    st.info("📊 **Dashboard**\n\nVisão geral com gráficos e estatísticas")

with col2:
    st.success("💳 **Contas a Pagar**\n\nGerencie todas as suas contas")

with col3:
    st.warning("📄 **Upload PDF**\n\nExtração automática de boletos")

# Footer
st.markdown("---")
st.markdown("🔧 Sistema desenvolvido com Streamlit + Python | Versão 1.0.0")

# Error monitoring section (debug)
if st.sidebar.checkbox('🔍 Debug Mode', value=False):
    st.sidebar.markdown('### System Status')
    try:
        from modules.database import get_db
        db = get_db()
        st.sidebar.success('✅ Database: Connected')
        db.close()
    except Exception as e:
        st.sidebar.error(f'❌ Database: {e}')
    
    try:
        from modules.pdf_parser import ocr_status
        st.sidebar.info(f'📄 {ocr_status()}')
    except Exception as e:
        st.sidebar.error(f'❌ PDF Parser: {e}')
    
    import os
    log_file = os.path.join('logs', f"app_{__import__('datetime').datetime.now().strftime('%Y%m%d')}.log")
    if os.path.exists(log_file):
        with open(log_file, 'r', encoding='utf-8') as f:
            recent_logs = f.readlines()[-50:]  # últimas 50 linhas
        with st.sidebar.expander('📋 Recent Logs'):
            st.text(''.join(recent_logs))
