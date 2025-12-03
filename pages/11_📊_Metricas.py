"""
Endpoint de Métricas e Health Checks
-------------------------------------
Adiciona rotas /metrics e /health ao app Streamlit.
"""
import streamlit as st
from modules.observability import get_metrics, get_health


def render_metrics_page():
    """Renderiza página de métricas Prometheus."""
    st.set_page_config(page_title="Métricas", page_icon="📊")
    st.title("📊 Métricas do Sistema")
    
    metrics = get_metrics()
    prometheus_text = metrics.export_prometheus()
    
    st.subheader("Formato Prometheus")
    st.code(prometheus_text, language='text')
    
    st.info("💡 Endpoint compatível com Prometheus para scraping automático.")


def render_health_page():
    """Renderiza página de health checks."""
    st.set_page_config(page_title="Health Check", page_icon="❤️")
    st.title("❤️ Status do Sistema")
    
    health = get_health()
    results = health.run_all()
    
    # Status geral
    if results['status'] == 'healthy':
        st.success("✅ Sistema operacional")
    else:
        st.error("❌ Sistema com problemas")
    
    st.metric("Timestamp", results['timestamp'])
    
    # Detalhes dos checks
    st.subheader("Componentes")
    for name, check_result in results['checks'].items():
        status = check_result['status']
        if status == 'pass':
            st.success(f"✅ {name.upper()}: Operacional")
        else:
            error_msg = check_result.get('error', 'Falha desconhecida')
            st.error(f"❌ {name.upper()}: {error_msg}")
    
    # JSON completo
    with st.expander("📋 JSON Completo"):
        st.json(results)


if __name__ == "__main__":
    # Detecta qual página renderizar baseado em query params
    import sys
    if len(sys.argv) > 1:
        if sys.argv[1] == 'metrics':
            render_metrics_page()
        elif sys.argv[1] == 'health':
            render_health_page()
    else:
        render_health_page()
