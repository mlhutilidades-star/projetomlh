"""
Sistema de Cache para Consultas Pesadas
----------------------------------------
Implementa cache em memória com TTL para otimizar queries do analytics.
"""
from typing import Any, Callable, Optional
from functools import wraps
from datetime import datetime, timedelta
import hashlib
import json


class SimpleCache:
    """Cache em memória com TTL por entrada."""
    
    def __init__(self, default_ttl_seconds: int = 300):
        """
        Args:
            default_ttl_seconds: Tempo padrão de vida do cache (5 minutos)
        """
        self._cache: dict[str, tuple[Any, datetime]] = {}
        self._default_ttl = default_ttl_seconds
    
    def _generate_key(self, func_name: str, args: tuple, kwargs: dict) -> str:
        """Gera chave única baseada em nome da função e argumentos."""
        # Serializa args/kwargs para criar hash estável
        args_str = json.dumps(args, sort_keys=True, default=str)
        kwargs_str = json.dumps(kwargs, sort_keys=True, default=str)
        combined = f"{func_name}:{args_str}:{kwargs_str}"
        return hashlib.md5(combined.encode()).hexdigest()
    
    def get(self, key: str) -> Optional[Any]:
        """Recupera valor do cache se não expirado."""
        if key in self._cache:
            value, expiry = self._cache[key]
            if datetime.now() < expiry:
                return value
            else:
                del self._cache[key]  # Limpeza de expirados
        return None
    
    def set(self, key: str, value: Any, ttl_seconds: Optional[int] = None):
        """Armazena valor no cache com TTL."""
        ttl = ttl_seconds if ttl_seconds is not None else self._default_ttl
        expiry = datetime.now() + timedelta(seconds=ttl)
        self._cache[key] = (value, expiry)
    
    def clear(self):
        """Limpa todo o cache."""
        self._cache.clear()
    
    def invalidate_pattern(self, pattern: str):
        """Remove entradas cujas chaves contêm o padrão."""
        to_delete = [k for k in self._cache.keys() if pattern in k]
        for k in to_delete:
            del self._cache[k]


# Instância global do cache
_global_cache = SimpleCache(default_ttl_seconds=300)


def cached(ttl_seconds: Optional[int] = None):
    """
    Decorator para cachear resultado de funções.
    
    Args:
        ttl_seconds: Tempo de vida do cache (padrão: 300s)
    
    Exemplo:
        @cached(ttl_seconds=600)
        def calcular_kpis():
            # consulta pesada...
            return kpis
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            cache_key = _global_cache._generate_key(func.__name__, args, kwargs)
            
            # Tenta recuperar do cache
            cached_value = _global_cache.get(cache_key)
            if cached_value is not None:
                return cached_value
            
            # Executa função e armazena resultado
            result = func(*args, **kwargs)
            _global_cache.set(cache_key, result, ttl_seconds)
            return result
        
        return wrapper
    return decorator


def clear_cache():
    """Limpa todo o cache global."""
    _global_cache.clear()


def invalidate_cache(pattern: str):
    """Invalida entradas de cache que contêm o padrão."""
    _global_cache.invalidate_pattern(pattern)
