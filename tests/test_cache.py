"""
Testes automatizados para o módulo de cache persistente com Redis.
"""

import time
from modules.cache import cache_set, cache_get, cache_clear

def test_cache_set_and_get():
    """
    Testa escrita e leitura básica do cache Redis.
    """
    cache_clear()
    cache_set('test_key', 'test_value', expire=10)
    result = cache_get('test_key')
    assert result == 'test_value', f"Esperado 'test_value', obtido {result}"

def test_cache_expiry():
    """
    Testa expiração automática de chaves no cache.
    """
    cache_clear()
    cache_set('expiring_key', 'expiring_value', expire=2)
    result_before = cache_get('expiring_key')
    assert result_before == 'expiring_value', "Valor deveria existir imediatamente após set"
    
    time.sleep(3)  # Aguarda expiração
    result_after = cache_get('expiring_key')
    assert result_after is None, f"Valor deveria ter expirado, mas obteve {result_after}"

def test_cache_clear():
    """
    Testa limpeza completa do cache.
    """
    cache_clear()
    cache_set('key1', 'value1', expire=10)
    cache_set('key2', 'value2', expire=10)
    
    cache_clear()
    
    result1 = cache_get('key1')
    result2 = cache_get('key2')
    assert result1 is None, "key1 deveria ter sido deletada"
    assert result2 is None, "key2 deveria ter sido deletada"
