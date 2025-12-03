import streamlit as st
import logging
from modules.sync_apis import sync_shopee_pedidos, get_sync_stats
from modules.database import get_all_contas
from datetime import datetime

logger = logging.getLogger(__name__)

st.set_page_config(page_title="Sincronizar Shopee", page_icon="🔄", layout="wide")

st.title("🔄 Sincronização Shopee")
st.markdown("**Importação automática de pedidos com dados financeiros completos**")

# Mostrar estatísticas atuais
st.subheader("📊 Estatísticas Atuais")
stats = get_sync_stats()
col1, col2, col3 = st.columns(3)
col1.metric("Total de Registros", stats['total_contas'])
col2.metric("Pedidos Shopee", stats['contas_shopee'])
col3.metric("Receita Shopee Total", f"R$ {stats.get('receita_shopee_total', 0):.2f}")

st.divider()

# Opções de sincronização
st.subheader("⚙️ Configurações de Sincronização")

st.info("""
💡 **Dados Importados da Shopee:**
- Receita bruta do pedido
- Taxas (comissão, serviço, transação)
- Custo de frete
- **Receita líquida calculada automaticamente**
- Status do pedido
- Informações do comprador
""")

dias_shopee = st.number_input(
    "📅 Shopee: Dias para trás (máx 15 dias pela API)",
    min_value=1,
    max_value=15,
    value=7,
    help="API Shopee permite até 15 dias retroativos"
)

st.divider()

# Botão de sincronização
if st.button("🚀 Sincronizar Pedidos Shopee", type="primary", use_container_width=True):
    with st.spinner("Sincronizando dados da Shopee..."):
        try:
            st.info("🛍️ Buscando pedidos Shopee e calculando valores financeiros...")
            resultado = sync_shopee_pedidos(dias_atras=dias_shopee)
            
            if 'erro' in resultado:
                st.error(f"❌ Erro: {resultado['erro']}")
                if 'mensagem' in resultado:
                    st.info(resultado['mensagem'])
            elif 'mensagem' in resultado:
                st.warning(resultado['mensagem'])
            else:
                st.success("✅ Sincronização Shopee finalizada!")
                
                col1, col2 = st.columns(2)
                col1.metric("Pedidos Importados", resultado['total_importados'])
                col2.metric("Erros", resultado['total_erros'])
                
                if resultado['pedidos']:
                    with st.expander("📋 Pedidos processados"):
                        for pedido in resultado['pedidos']:
                            st.write(f"- {pedido}")
            
            # Atualizar estatísticas
            st.rerun()
            
        except Exception as e:
            st.error(f"❌ Erro durante sincronização: {str(e)}")
            logger.error(f"Erro na sincronização: {e}", exc_info=True)

st.divider()

# Últimos pedidos importados
st.subheader("📝 Últimos 10 Pedidos Shopee")
contas = get_all_contas()
contas_shopee = [c for c in contas if 'Shopee' in c.get('categoria', '')]

if contas_shopee:
    import pandas as pd
    df = pd.DataFrame([{
        'ID': c['id'],
        'Comprador': c['fornecedor'],
        'Receita Líquida': f"R$ {c['valor']:.2f}",
        'Data': c['vencimento'],
        'Status': c['status'],
        'Order SN': c['linha_digitavel']
    } for c in contas_shopee[-10:][::-1]])  # Últimos 10, ordem reversa
    
    st.dataframe(df, use_container_width=True, hide_index=True)
else:
    st.info("Nenhum pedido Shopee sincronizado ainda. Clique em 'Sincronizar' acima.")

# Informações e ajuda
with st.expander("ℹ️ Informações sobre Sincronização Shopee"):
    st.markdown("""
    ### Como funciona
    
    **Dados Financeiros Importados:**
    1. **Receita Bruta:** Valor total pago pelo comprador
    2. **Taxas Shopee:**
       - Taxa de comissão (commission_fee)
       - Taxa de serviço (service_fee)
       - Taxa de transação (transaction_fee)
    3. **Frete:** Custo real de envio
    4. **Receita Líquida:** Calculada como Receita Bruta - Total de Taxas
    
    **Processo de Importação:**
    1. Busca lista de pedidos (últimos X dias)
    2. Obtém detalhes completos de cada pedido
    3. Calcula valores financeiros
    4. Cria registro no sistema com todas as informações
    
    **Informações Salvas:**
    - Order SN (identificador único)
    - Status do pedido
    - Nome do comprador
    - Quantidade de itens
    - Breakdown completo de valores
    - Data de pagamento
    
    ### Credenciais Necessárias
    
    Configure no arquivo `.env`:
    - `SHOPEE_PARTNER_ID` ✅
    - `SHOPEE_PARTNER_KEY` ✅
    - `SHOPEE_SHOP_ID` ✅
    - `SHOPEE_ACCESS_TOKEN` (obtido via OAuth)
    - `SHOPEE_REFRESH_TOKEN` (para renovação automática)
    
    ### OAuth Setup
    
    Para obter access_token:
    ```bash
    python setup_shopee_oauth.py
    ```
    
    Ou consulte: `SHOPEE_OAUTH_SETUP.md`
    
    ### Limitações da API
    - Máximo 15 dias retroativos
    - Rate limit: ~1 req/segundo
    - Access token expira em 4 horas
    - Máximo 50 pedidos por chamada de detalhes
    
    ### Frequência Recomendada
    - **Produção:** 1-2x por dia
    - **Desenvolvimento:** Conforme necessário
    - **Automação:** Configure cron/scheduler
    
    ### Logs
    Todas as operações são registradas em `logs/app_YYYYMMDD.log`
    """)

# Footer com última atualização
st.caption(f"Última visualização: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")

