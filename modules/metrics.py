"""
Módulo de Métricas de Performance para HUB Financeiro MLH.
Coleta e registra métricas de tempo de execução, cache hit/miss e performance.
"""

import time
from functools import wraps
from datetime import datetime
from typing import Callable, Any, Dict
import json
from pathlib import Path

# Diretório para armazenar métricas
METRICS_DIR = Path(__file__).parent.parent / "data" / "metrics"
METRICS_DIR.mkdir(parents=True, exist_ok=True)


class MetricsCollector:
    """Coletor centralizado de métricas de performance."""
    
    def __init__(self):
        self.metrics = {}
        self.cache_stats = {"hits": 0, "misses": 0}
    
    def record_execution_time(self, function_name: str, duration: float, metadata: Dict = None):
        """
        Registra tempo de execução de uma função.
        
        Args:
            function_name (str): Nome da função.
            duration (float): Duração em segundos.
            metadata (Dict): Metadados adicionais (opcional).
        """
        if function_name not in self.metrics:
            self.metrics[function_name] = []
        
        record = {
            "timestamp": datetime.now().isoformat(),
            "duration": duration,
            "metadata": metadata or {}
        }
        self.metrics[function_name].append(record)
        
        # Limitar histórico a últimas 1000 execuções por função
        if len(self.metrics[function_name]) > 1000:
            self.metrics[function_name] = self.metrics[function_name][-1000:]
    
    def record_cache_hit(self):
        """Registra um acerto de cache."""
        self.cache_stats["hits"] += 1
    
    def record_cache_miss(self):
        """Registra uma falha de cache."""
        self.cache_stats["misses"] += 1
    
    def get_stats(self, function_name: str = None) -> Dict:
        """
        Retorna estatísticas de performance.
        
        Args:
            function_name (str): Nome da função (None para todas).
        
        Returns:
            Dict: Estatísticas consolidadas.
        """
        if function_name:
            executions = self.metrics.get(function_name, [])
            if not executions:
                return {}
            
            durations = [e["duration"] for e in executions]
            return {
                "function": function_name,
                "total_calls": len(durations),
                "avg_duration": sum(durations) / len(durations),
                "min_duration": min(durations),
                "max_duration": max(durations),
                "total_duration": sum(durations)
            }
        
        # Retorna estatísticas de todas as funções
        stats = {}
        for func_name in self.metrics:
            stats[func_name] = self.get_stats(func_name)
        
        stats["cache"] = {
            "hits": self.cache_stats["hits"],
            "misses": self.cache_stats["misses"],
            "hit_rate": (self.cache_stats["hits"] / (self.cache_stats["hits"] + self.cache_stats["misses"]))
                        if (self.cache_stats["hits"] + self.cache_stats["misses"]) > 0 else 0
        }
        
        return stats
    
    def export_metrics(self, filename: str = "metrics.json"):
        """
        Exporta métricas para arquivo JSON.
        
        Args:
            filename (str): Nome do arquivo.
        """
        filepath = METRICS_DIR / filename
        with open(filepath, "w") as f:
            json.dump(self.get_stats(), f, indent=2, default=str)
    
    def clear_metrics(self):
        """Limpa todas as métricas coletadas."""
        self.metrics = {}
        self.cache_stats = {"hits": 0, "misses": 0}


# Instância global do collector
_metrics_collector = MetricsCollector()


def measure_performance(cache_aware=False):
    """
    Decorator para medir performance de funções.
    
    Args:
        cache_aware (bool): Se True, registra cache hits/misses.
    
    Exemplo:
        @measure_performance(cache_aware=True)
        def fetch_shopee_orders():
            pass
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                duration = time.time() - start_time
                metadata = {
                    "args_count": len(args),
                    "kwargs_keys": list(kwargs.keys())
                }
                _metrics_collector.record_execution_time(func.__name__, duration, metadata)
        
        return wrapper
    return decorator


def record_cache_access(hit: bool):
    """
    Registra acesso ao cache.
    
    Args:
        hit (bool): True se foi cache hit, False para cache miss.
    """
    if hit:
        _metrics_collector.record_cache_hit()
    else:
        _metrics_collector.record_cache_miss()


def get_metrics(function_name: str = None) -> Dict:
    """
    Retorna métricas coletadas.
    
    Args:
        function_name (str): Nome da função (None para todas).
    
    Returns:
        Dict: Estatísticas de performance.
    """
    return _metrics_collector.get_stats(function_name)


def export_metrics(filename: str = "metrics.json"):
    """
    Exporta métricas para arquivo.
    
    Args:
        filename (str): Nome do arquivo para exportar.
    """
    _metrics_collector.export_metrics(filename)


def clear_metrics():
    """Limpa todas as métricas coletadas."""
    _metrics_collector.clear_metrics()
