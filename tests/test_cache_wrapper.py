"""
Testes para o módulo de cache_wrapper.
"""

import pytest
import json
from modules.cache_wrapper import (
    generate_cache_key,
    cached_api_call,
    CachedAPI,
    invalidate_api_cache,
    clear_all_cache
)
from modules.metrics import clear_metrics, get_metrics


def test_generate_cache_key():
    """Testa geração de chave de cache."""
    key1 = generate_cache_key("arg1", "arg2", kwarg1="value1")
    key2 = generate_cache_key("arg1", "arg2", kwarg1="value1")
    key3 = generate_cache_key("arg1", "arg2", kwarg1="value2")
    
    # Mesmos argumentos devem gerar mesma chave
    assert key1 == key2
    # Argumentos diferentes devem gerar chaves diferentes
    assert key1 != key3
    # Chave deve ser string de 32 caracteres (MD5)
    assert len(key1) == 32


def test_cached_api_call_decorator():
    """Testa decorator de cache para chamadas de API."""
    clear_metrics()
    clear_all_cache()
    
    call_count = [0]
    
    @cached_api_call(ttl=10, key_prefix="test_")
    def mock_api_call(param):
        call_count[0] += 1
        return {"result": f"data_{param}", "calls": call_count[0]}
    
    # Primeira chamada - sem cache
    result1 = mock_api_call("value1")
    assert result1["calls"] == 1
    
    # Segunda chamada com mesmo parâmetro - com cache
    result2 = mock_api_call("value1")
    assert result2["calls"] == 1  # Mesma chamada original
    
    # Terceira chamada com parâmetro diferente - sem cache
    result3 = mock_api_call("value2")
    assert result3["calls"] == 2  # Nova chamada
    
    # Verificar métricas de cache
    stats = get_metrics()
    assert stats["cache"]["hits"] == 1
    assert stats["cache"]["misses"] == 2


def test_cached_api_call_with_dict_result():
    """Testa cache com resultados complexos (dicts)."""
    clear_all_cache()
    
    call_count = [0]
    
    @cached_api_call(ttl=10, key_prefix="dict_")
    def api_returns_dict():
        call_count[0] += 1
        return {
            "orders": [
                {"id": 1, "value": 100},
                {"id": 2, "value": 200}
            ],
            "total": 300
        }
    
    result1 = api_returns_dict()
    result2 = api_returns_dict()
    
    assert result1 == result2
    assert call_count[0] == 1  # Função apenas executada uma vez


def test_cached_api_class():
    """Testa classe CachedAPI."""
    clear_all_cache()
    clear_metrics()
    
    class MockShopeeAPI(CachedAPI):
        cache_prefix = "shopee_"
        cache_ttl = 3600
        
        def get_orders(self, shop_id):
            # Simula chamada com cache
            cached = self.get_cached(shop_id)
            if cached is not None:
                return cached
            
            result = {"shop_id": shop_id, "orders": []}
            self.set_cached(result, shop_id)
            return result
    
    api = MockShopeeAPI()
    
    # Primeira chamada
    result1 = api.get_orders(123)
    # Segunda chamada - deve estar em cache
    result2 = api.get_orders(123)
    
    assert result1 == result2
    
    # Verificar que cache foi usado
    stats = get_metrics()
    assert stats["cache"]["hits"] >= 1


def test_cached_api_disable_cache():
    """Testa desabilitação de cache."""
    clear_all_cache()
    
    class TestAPI(CachedAPI):
        cache_prefix = "test_"
        
        def __init__(self):
            super().__init__()
            self.call_count = 0
        
        def expensive_call(self, param="default"):
            self.call_count += 1
            # Simula cache manualmente
            cached = self.get_cached(param)
            if cached is not None:
                return cached
            
            result = {"count": self.call_count, "param": param}
            self.set_cached(result, param)
            return result
    
    api = TestAPI()
    
    # Com cache habilitado
    result1 = api.expensive_call("test")
    result2 = api.expensive_call("test")
    assert result1["count"] == result2["count"]  # Cache
    
    # Desabilitar cache
    api.disable_cache()
    result3 = api.expensive_call("test")
    assert result3["count"] != result1["count"]  # Sem cache


def test_invalidate_cache_prefix():
    """Testa invalidação de cache por prefixo."""
    clear_all_cache()
    
    @cached_api_call(ttl=10, key_prefix="api_")
    def api_call(value):
        return {"data": value}
    
    # Popula cache
    api_call("value1")
    api_call("value2")
    api_call("value3")
    
    # Invalida prefixo
    invalidate_api_cache("api_")
    
    # Nova chamada não usará cache
    clear_metrics()
    result = api_call("value1")
    stats = get_metrics()
    assert stats["cache"]["misses"] == 1  # Miss após invalidação


def test_cache_with_none_result():
    """Testa cache com resultado None."""
    clear_all_cache()
    
    call_count = [0]
    
    @cached_api_call(ttl=10, key_prefix="none_")
    def returns_none():
        call_count[0] += 1
        return None
    
    result1 = returns_none()
    result2 = returns_none()
    
    assert result1 is None
    assert result2 is None
    # None não é cacheado, então a função é chamada duas vezes
    assert call_count[0] == 2
