import streamlit as st
from modules.shopee_api import listar_pedidos, listar_produtos
from modules import config
from modules.database import get_db, ContaPagar, init_database
import subprocess, sys, os, time, datetime

st.title("🛍️ Shopee Integration")

# Verificar configuração OAuth
st.subheader("📋 Status de Configuração")
col1, col2, col3, col4 = st.columns(4)
col1.metric("Partner ID", "✅" if config.SHOPEE_PARTNER_ID else "❌")
col2.metric("Partner Key", "✅" if config.SHOPEE_PARTNER_KEY else "❌")
col3.metric("Shop ID", "✅" if config.SHOPEE_SHOP_ID else "❌")
col4.metric("Access Token", "✅" if config.SHOPEE_ACCESS_TOKEN else "❌")

if not config.SHOPEE_ACCESS_TOKEN:
    st.warning("⚠️ **OAuth não configurado**")
    st.info("""
    A Shopee API v2 requer OAuth 2.0 para acessar dados da loja.
    
    **Para configurar:**
    1. Execute o script: `python setup_shopee_oauth.py`
    2. Siga as instruções para obter access_token
    3. Configure no arquivo .env
    
    Ou consulte o guia completo em: `SHOPEE_OAUTH_SETUP.md`
    """)
    
    with st.expander("📖 Ver Guia de Configuração Rápida"):
        st.markdown("""
        ### Passos Rápidos
        
        1. **Abra terminal na pasta do projeto**
        2. **Execute:** 
           ```bash
           python setup_shopee_oauth.py
           ```
        3. **Siga as instruções** para autorizar no navegador
        4. **Cole o code** quando solicitado
        5. **Reinicie** o Streamlit
        
        ### Alternativa Manual
        
        Se preferir exportar dados manualmente:
        - Acesse Shopee Seller Center
        - Exporte pedidos como CSV
        - Importe via página "📥 Importação"
        """)
else:
    st.success("✅ OAuth configurado! Access token presente.")

st.divider()

# Testar conexão
st.subheader("🔄 Testar Conexão")

col1, col2 = st.columns(2)

with col1:
    if st.button("📦 Listar Produtos", use_container_width=True):
        with st.spinner("Buscando produtos..."):
            resultado = listar_produtos(page_size=10, offset=0)
            
            if 'error' in resultado:
                st.error(f"❌ Erro: {resultado['error']}")
                if 'info' in resultado:
                    st.info(resultado['info'])
                if 'instrucoes' in resultado:
                    st.markdown("**Instruções:**")
                    for instrucao in resultado['instrucoes']:
                        st.write(f"- {instrucao}")
            else:
                items = resultado.get('items', [])
                st.success(f"✅ {len(items)} produtos retornados")
                if items:
                    st.json(items[:5])

with col2:
    if st.button("📋 Listar Pedidos", use_container_width=True):
        with st.spinner("Buscando pedidos..."):
            # Últimas 48h
            time_to = int(time.time())
            time_from = time_to - (2 * 24 * 3600)
            
            resultado = listar_pedidos(time_from=time_from, time_to=time_to)
            
            if 'error' in resultado:
                st.error(f"❌ Erro: {resultado['error']}")
                if 'mensagem' in resultado:
                    st.info(resultado['mensagem'])
                if 'instrucoes' in resultado:
                    st.markdown("**Instruções:**")
                    for instrucao in resultado['instrucoes']:
                        st.write(f"- {instrucao}")
                if 'documentacao' in resultado:
                    st.markdown(f"📚 [Documentação Oficial]({resultado['documentacao']})")
            else:
                orders = resultado.get('order_list', [])
                st.success(f"✅ {len(orders)} pedidos retornados")
                if orders:
                    st.json(orders[:5])
                
                if resultado.get('more'):
                    st.info(f"Há mais pedidos. Use cursor: {resultado.get('next_cursor', '')}")

st.divider()

# Sincronização estendida (últimos 90 dias)
st.subheader("🗂️ Sincronização de Pedidos (Histórico)")
col_sync1, col_sync2 = st.columns([1,1])
with col_sync1:
    if st.button("📥 Importar últimos 90 dias", use_container_width=True):
        with st.spinner("Sincronizando pedidos Shopee (até 90 dias)..."):
            # Chamar script diretamente para reutilizar lógica
            cmd = [sys.executable, os.path.join(os.getcwd(), "sync_shopee_90d.py"), "90"]
            try:
                completed = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
                st.success("✅ Sincronização concluída")
                with st.expander("📄 Log da sincronização"):
                    st.code(completed.stdout[-4000:] or "(sem saída)")
                if completed.stderr:
                    st.warning("⚠️ STDERR presente")
                    st.code(completed.stderr[-2000:])
            except subprocess.TimeoutExpired:
                st.error("⏱️ Timeout na sincronização (10 min). Tente novamente.")
            except Exception as e:
                st.error(f"❌ Erro ao sincronizar: {e}")
with col_sync2:
    if st.button("🧮 Resumo de Pedidos Shopee", use_container_width=True):
        init_database()
        db = get_db()
        try:
            total_contas = db.query(ContaPagar).filter(ContaPagar.descricao.like('%Pedido Shopee%')).count()
            ultimos_30 = db.query(ContaPagar).filter(ContaPagar.descricao.like('%Pedido Shopee%'), ContaPagar.vencimento >= (datetime.date.today() - datetime.timedelta(days=30))).count()
            st.info(f"Total de pedidos Shopee no banco: {total_contas}\nÚltimos 30 dias: {ultimos_30}")
        finally:
            db.close()
        
st.caption("Use a sincronização para preencher histórico antes de análises e dashboards.")

# Informações úteis
with st.expander("ℹ️ Sobre a Integração Shopee"):
    st.markdown("""
    ### API Shopee v2 (OAuth 2.0)
    
    A Shopee mudou completamente sua API em 2023 para OAuth 2.0.
    Agora é necessário:
    
    - ✅ Partner ID (configurado)
    - ✅ Partner Key (configurado)  
    - ✅ Shop ID (configurado)
    - ❌ Access Token (requer OAuth flow)
    
    ### Como Obter Access Token
    
    **Opção 1: Script Automatizado (Recomendado)**
    ```bash
    python setup_shopee_oauth.py
    ```
    
    **Opção 2: Manual**
    1. Acesse Shopee Partner Portal
    2. Configure OAuth na sua aplicação
    3. Obtenha authorization code
    4. Troque por access_token via API
    
    ### Documentação
    - [Shopee API v2](https://open.shopee.com/documents/v2/)
    - [Authentication](https://open.shopee.com/documents/v2/v2.public.authentication)
    - [Order API](https://open.shopee.com/documents/v2/v2.order.get_order_list)
    
    ### Limitações
    - Access token expira em 4 horas
    - Requer refresh token para renovação automática
    - Rate limits aplicam (ver documentação)
    """)

# Footer
st.caption("Shopee API v2 - Requer OAuth 2.0 configurado")
