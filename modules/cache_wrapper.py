"""
Wrapper de Cache para integração com APIs.
Fornece decoradores e funções para cachear chamadas de API.
"""

import json
import hashlib
from functools import wraps
from typing import Callable, Any, Optional

from .cache import cache_get, cache_set, cache_clear
from .metrics import measure_performance, record_cache_access


def generate_cache_key(*args, **kwargs) -> str:
    """
    Gera uma chave única para cache baseada em argumentos.
    
    Args:
        *args: Argumentos posicionais
        **kwargs: Argumentos nomeados
    
    Returns:
        str: Hash MD5 como chave de cache
    """
    # Cria string representando os argumentos
    arg_string = json.dumps({
        "args": [str(arg) for arg in args],
        "kwargs": {k: str(v) for k, v in sorted(kwargs.items())}
    }, sort_keys=True)
    
    # Retorna hash MD5 da string
    return hashlib.md5(arg_string.encode()).hexdigest()


def cached_api_call(ttl: int = 3600, key_prefix: str = ""):
    """
    Decorator para cachear resultados de chamadas de API.
    
    Args:
        ttl (int): Tempo de vida em cache (segundos). Padrão: 1 hora.
        key_prefix (str): Prefixo para chave de cache (ex: "shopee_orders_").
    
    Exemplo:
        @cached_api_call(ttl=1800, key_prefix="shopee_")
        def get_shopee_orders(shop_id):
            return api_call(shop_id)
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        @measure_performance()
        def wrapper(*args, **kwargs):
            # Gera chave de cache
            cache_key = f"{key_prefix}{generate_cache_key(*args, **kwargs)}"
            
            # Tenta recuperar do cache
            cached_result = cache_get(cache_key)
            if cached_result is not None:
                record_cache_access(hit=True)
                return json.loads(cached_result)
            
            # Cache miss - executa função
            record_cache_access(hit=False)
            result = func(*args, **kwargs)
            
            # Armazena resultado em cache
            if result is not None:
                cache_set(cache_key, json.dumps(result), expire=ttl)
            
            return result
        
        return wrapper
    return decorator


def invalidate_api_cache(key_prefix: str):
    """
    Invalida todas as chaves de cache com um prefixo específico.
    
    Args:
        key_prefix (str): Prefixo das chaves a invalidar (ex: "shopee_").
    
    Nota: Usa wildcard pattern. Redis deve estar disponível.
    """
    try:
        from .cache import get_redis_client
        client = get_redis_client()
        keys = client.keys(f"{key_prefix}*")
        if keys:
            client.delete(*keys)
    except Exception as e:
        print(f"Erro ao invalidar cache: {e}")


def clear_all_cache():
    """Limpa todo o cache de APIs."""
    cache_clear()


class CachedAPI:
    """Classe base para APIs com suporte a cache."""
    
    cache_ttl = 3600  # 1 hora por padrão
    cache_prefix = ""
    
    def __init__(self):
        self.cache_enabled = True
    
    def enable_cache(self):
        """Habilita cache para esta API."""
        self.cache_enabled = True
    
    def disable_cache(self):
        """Desabilita cache para esta API."""
        self.cache_enabled = False
    
    def clear_cache(self):
        """Limpa cache desta API."""
        invalidate_api_cache(self.cache_prefix)
    
    def get_cache_key(self, *args, **kwargs) -> str:
        """Gera chave de cache para argumentos."""
        return f"{self.cache_prefix}{generate_cache_key(*args, **kwargs)}"
    
    def get_cached(self, *args, **kwargs):
        """Recupera valor do cache."""
        if not self.cache_enabled:
            return None
        
        key = self.get_cache_key(*args, **kwargs)
        result = cache_get(key)
        if result:
            record_cache_access(hit=True)
            return json.loads(result)
        
        record_cache_access(hit=False)
        return None
    
    def set_cached(self, value, *args, **kwargs):
        """Armazena valor em cache."""
        if not self.cache_enabled:
            return
        
        key = self.get_cache_key(*args, **kwargs)
        cache_set(key, json.dumps(value), expire=self.cache_ttl)
