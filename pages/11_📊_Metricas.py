"""
Dashboard de Métricas de Performance - Phase 10.
Página Streamlit para visualizar e monitorar performance da aplicação.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

try:
    from modules.auth import require_role
    from modules.metrics import get_metrics, export_metrics
    IMPORTS_OK = True
except ImportError as e:
    IMPORTS_OK = False
    import_error = str(e)


def render_page():
    """Renderiza página de métricas de performance."""
    st.set_page_config(page_title="📊 Métricas", layout="wide")
    
    st.title("📊 Métricas de Performance")
    st.markdown("Sistema de monitoramento de performance e cache da aplicação.")
    st.markdown("---")
    
    if not IMPORTS_OK:
        st.error(f"❌ Erro ao importar módulos: {import_error}")
        return
    
    # Recuperar métricas
    try:
        metrics = get_metrics()
    except Exception as e:
        st.error(f"Erro ao recuperar métricas: {e}")
        return
    
    if not metrics:
        st.info("ℹ️ Nenhuma métrica coletada ainda. Execute algumas operações para gerar dados.")
        return
    
    # Tabs para diferentes visualizações
    tab1, tab2, tab3 = st.tabs(["Performance de Funções", "Estatísticas de Cache", "Exportar Dados"])
    
    with tab1:
        st.subheader("Performance de Funções")
        
        # Filtrar apenas métricas de funções (não cache)
        function_metrics = {k: v for k, v in metrics.items() if k != "cache" and v}
        
        if function_metrics:
            # Dataframe com métricas de funções
            data = []
            for func_name, stats in function_metrics.items():
                if isinstance(stats, dict) and "total_calls" in stats:
                    data.append({
                        "Função": func_name,
                        "Total de Chamadas": stats.get("total_calls", 0),
                        "Tempo Médio (s)": round(stats.get("avg_duration", 0), 4),
                        "Tempo Mínimo (s)": round(stats.get("min_duration", 0), 4),
                        "Tempo Máximo (s)": round(stats.get("max_duration", 0), 4),
                        "Tempo Total (s)": round(stats.get("total_duration", 0), 2)
                    })
            
            if data:
                df = pd.DataFrame(data)
                
                # Coluna 1: Tabela
                col1, col2 = st.columns([1, 1])
                
                with col1:
                    st.dataframe(df, use_container_width=True)
                
                with col2:
                    # Gráfico de tempo médio por função
                    if len(data) > 0:
                        fig = px.bar(
                            df,
                            x="Função",
                            y="Tempo Médio (s)",
                            title="Tempo Médio de Execução por Função",
                            color="Tempo Médio (s)",
                            color_continuous_scale="Viridis"
                        )
                        st.plotly_chart(fig, use_container_width=True)
                
                # Gráfico de total de chamadas
                if len(data) > 1:
                    fig_calls = px.pie(
                        df,
                        values="Total de Chamadas",
                        names="Função",
                        title="Distribuição de Chamadas por Função"
                    )
                    st.plotly_chart(fig_calls, use_container_width=True)
        else:
            st.info("ℹ️ Nenhuma métrica de função disponível.")
    
    with tab2:
        st.subheader("Estatísticas de Cache")
        
        cache_stats = metrics.get("cache", {})
        
        if cache_stats:
            # Métricas principais do cache
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric(
                    "Cache Hits",
                    cache_stats.get("hits", 0),
                    delta=None
                )
            
            with col2:
                st.metric(
                    "Cache Misses",
                    cache_stats.get("misses", 0),
                    delta=None
                )
            
            with col3:
                hit_rate = cache_stats.get("hit_rate", 0)
                st.metric(
                    "Hit Rate",
                    f"{hit_rate:.1%}",
                    delta=None
                )
            
            with col4:
                total = cache_stats.get("hits", 0) + cache_stats.get("misses", 0)
                st.metric(
                    "Total de Acessos",
                    total,
                    delta=None
                )
            
            # Gráfico de hits vs misses
            fig = go.Figure(data=[
                go.Bar(
                    x=["Hits", "Misses"],
                    y=[cache_stats.get("hits", 0), cache_stats.get("misses", 0)],
                    marker=dict(color=["#2ecc71", "#e74c3c"])
                )
            ])
            fig.update_layout(title="Cache Hits vs Misses", height=400)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("ℹ️ Nenhuma estatística de cache disponível.")
    
    with tab3:
        st.subheader("Exportar Dados de Métricas")
        
        # Opções de exportação
        col1, col2 = st.columns([2, 1])
        
        with col1:
            filename = st.text_input(
                "Nome do arquivo",
                value=f"metrics_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            )
        
        with col2:
            if st.button("📥 Exportar para JSON", use_container_width=True):
                try:
                    export_metrics(filename)
                    st.success(f"✅ Métricas exportadas para: data/metrics/{filename}")
                except Exception as e:
                    st.error(f"❌ Erro ao exportar: {e}")
        
        # Mostrar dados brutos
        st.subheader("Dados Brutos de Métricas")
        st.json(metrics)




if __name__ == "__main__":
    render_page()

