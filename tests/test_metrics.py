"""
Testes para o módulo de métricas de performance.
"""

import pytest
import time
from modules.metrics import (
    measure_performance,
    record_cache_access,
    get_metrics,
    clear_metrics,
    MetricsCollector
)


def test_metrics_collector_record_execution():
    """Testa gravação de tempo de execução."""
    collector = MetricsCollector()
    
    collector.record_execution_time("test_func", 1.5, {"param": "value"})
    
    stats = collector.get_stats("test_func")
    assert stats["function"] == "test_func"
    assert stats["total_calls"] == 1
    assert stats["avg_duration"] == 1.5
    assert stats["min_duration"] == 1.5
    assert stats["max_duration"] == 1.5


def test_metrics_collector_multiple_executions():
    """Testa coleta de múltiplas execuções."""
    collector = MetricsCollector()
    
    collector.record_execution_time("func", 1.0)
    collector.record_execution_time("func", 2.0)
    collector.record_execution_time("func", 3.0)
    
    stats = collector.get_stats("func")
    assert stats["total_calls"] == 3
    assert stats["avg_duration"] == 2.0
    assert stats["min_duration"] == 1.0
    assert stats["max_duration"] == 3.0
    assert stats["total_duration"] == 6.0


def test_metrics_cache_stats():
    """Testa coleta de estatísticas de cache."""
    collector = MetricsCollector()
    
    collector.record_cache_hit()
    collector.record_cache_hit()
    collector.record_cache_miss()
    
    stats = collector.get_stats()
    assert stats["cache"]["hits"] == 2
    assert stats["cache"]["misses"] == 1
    assert stats["cache"]["hit_rate"] == pytest.approx(2/3, rel=0.01)


def test_measure_performance_decorator():
    """Testa decorator de medição de performance."""
    clear_metrics()
    
    @measure_performance()
    def slow_function():
        time.sleep(0.1)
        return "result"
    
    result = slow_function()
    
    assert result == "result"
    stats = get_metrics("slow_function")
    assert stats["total_calls"] == 1
    assert stats["avg_duration"] >= 0.1


def test_record_cache_access():
    """Testa registro de acesso ao cache."""
    clear_metrics()
    
    record_cache_access(hit=True)
    record_cache_access(hit=True)
    record_cache_access(hit=False)
    
    stats = get_metrics()
    assert stats["cache"]["hits"] == 2
    assert stats["cache"]["misses"] == 1


def test_metrics_collector_clear():
    """Testa limpeza de métricas."""
    collector = MetricsCollector()
    
    collector.record_execution_time("func", 1.5)
    collector.record_cache_hit()
    
    collector.clear_metrics()
    
    stats = collector.get_stats()
    assert len(stats) == 1  # Apenas cache stats retorna vazio
    assert stats["cache"]["hits"] == 0
    assert stats["cache"]["misses"] == 0


def test_metrics_history_limit():
    """Testa limite de histórico (1000 execuções por função)."""
    collector = MetricsCollector()
    
    # Registra 1100 execuções
    for i in range(1100):
        collector.record_execution_time("func", float(i))
    
    # Verificar que apenas as últimas 1000 estão armazenadas
    assert len(collector.metrics["func"]) == 1000


def test_get_metrics_all_functions():
    """Testa retorno de métricas para todas as funções."""
    clear_metrics()
    
    @measure_performance()
    def func_a():
        return "a"
    
    @measure_performance()
    def func_b():
        return "b"
    
    func_a()
    func_b()
    func_b()
    
    stats = get_metrics()
    assert "func_a" in stats
    assert "func_b" in stats
    assert stats["func_a"]["total_calls"] == 1
    assert stats["func_b"]["total_calls"] == 2
