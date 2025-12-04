"""
Módulo de cache persistente com Redis para HUB Financeiro MLH.
Substitui o cache em memória por uma solução persistente e escalável.
"""

import os

try:
    if os.getenv('TESTING'):
        import fakeredis
        REDIS_AVAILABLE = True
        _redis_module = fakeredis
    else:
        import redis
        REDIS_AVAILABLE = True
        _redis_module = redis
except ImportError:
    REDIS_AVAILABLE = False
    _redis_module = None

# Cache de cliente global para evitar múltiplas conexões
_client_cache = None


def get_redis_client():
    """
    Retorna um cliente Redis conectado ao localhost:6379 ou fake Redis em testes.
    Usa cache de cliente global para reutilizar a mesma conexão.
    
    Returns:
        redis.Redis: Cliente Redis configurado.
    """
    global _client_cache
    
    if not REDIS_AVAILABLE:
        raise RuntimeError("Redis não está instalado. Execute: pip install redis")
    
    if _client_cache is not None:
        return _client_cache
    
    if os.getenv('TESTING'):
        _client_cache = _redis_module.FakeStrictRedis(decode_responses=True)
    else:
        _client_cache = _redis_module.Redis(host='localhost', port=6379, db=0, decode_responses=True)
    
    return _client_cache


def cache_set(key, value, expire=3600):
    """
    Salva um valor no cache Redis com tempo de expiração (segundos).
    
    Args:
        key (str): Chave do cache.
        value (Any): Valor a ser armazenado.
        expire (int): Tempo de expiração em segundos (padrão: 3600).
    """
    if not REDIS_AVAILABLE:
        return  # Silenciosamente falha se Redis não está disponível
    try:
        client = get_redis_client()
        client.set(key, value, ex=expire)
    except Exception as e:
        print(f"Erro ao salvar no cache: {e}")


def cache_get(key):
    """
    Recupera um valor do cache Redis.
    
    Args:
        key (str): Chave do cache.
    
    Returns:
        Any: Valor armazenado ou None se não encontrado/expirado.
    """
    if not REDIS_AVAILABLE:
        return None
    try:
        client = get_redis_client()
        return client.get(key)
    except Exception as e:
        print(f"Erro ao recuperar do cache: {e}")
        return None


def cache_clear():
    """
    Limpa todo o cache Redis.
    """
    if not REDIS_AVAILABLE:
        return  # Silenciosamente falha se Redis não está disponível
    try:
        client = get_redis_client()
        client.flushdb()
    except Exception as e:
        print(f"Erro ao limpar cache: {e}")
