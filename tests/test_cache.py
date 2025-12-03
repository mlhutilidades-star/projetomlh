"""
Testes para o módulo de cache (modules/cache.py)
"""
import pytest
from datetime import datetime, timedelta
from modules.cache import SimpleCache, cached, clear_cache, invalidate_cache


class TestSimpleCache:
    """Tests for SimpleCache class"""
    
    def test_cache_set_and_get(self):
        """Test basic cache set and get"""
        cache = SimpleCache(default_ttl_seconds=60)
        cache.set("test_key", "test_value")
        
        result = cache.get("test_key")
        assert result == "test_value"
    
    def test_cache_expiry(self):
        """Test cache expiration"""
        cache = SimpleCache(default_ttl_seconds=0)  # Expires immediately
        cache.set("test_key", "test_value", ttl_seconds=0)
        
        # Should be expired
        result = cache.get("test_key")
        assert result is None
    
    def test_cache_clear(self):
        """Test cache clearing"""
        cache = SimpleCache()
        cache.set("key1", "value1")
        cache.set("key2", "value2")
        
        cache.clear()
        
        assert cache.get("key1") is None
        assert cache.get("key2") is None
    
    def test_cache_invalidate_pattern(self):
        """Test pattern-based cache invalidation"""
        cache = SimpleCache()
        cache.set("user_123_data", {"name": "John"})
        cache.set("user_456_data", {"name": "Jane"})
        cache.set("product_789", {"name": "Widget"})
        
        cache.invalidate_pattern("user_")
        
        assert cache.get("user_123_data") is None
        assert cache.get("user_456_data") is None
        assert cache.get("product_789") is not None
    
    def test_generate_key_consistency(self):
        """Test that key generation is consistent"""
        cache = SimpleCache()
        
        key1 = cache._generate_key("func", (1, 2), {"a": 3})
        key2 = cache._generate_key("func", (1, 2), {"a": 3})
        
        assert key1 == key2
    
    def test_generate_key_different_for_different_args(self):
        """Test that different args generate different keys"""
        cache = SimpleCache()
        
        key1 = cache._generate_key("func", (1, 2), {})
        key2 = cache._generate_key("func", (3, 4), {})
        
        assert key1 != key2


class TestCachedDecorator:
    """Tests for @cached decorator"""
    
    def setup_method(self):
        """Clear cache before each test"""
        clear_cache()
    
    def test_cached_decorator_basic(self):
        """Test basic caching behavior"""
        call_count = 0
        
        @cached(ttl_seconds=60)
        def expensive_function(x):
            nonlocal call_count
            call_count += 1
            return x * 2
        
        # First call
        result1 = expensive_function(5)
        assert result1 == 10
        assert call_count == 1
        
        # Second call should use cache
        result2 = expensive_function(5)
        assert result2 == 10
        assert call_count == 1  # Not incremented
    
    def test_cached_decorator_different_args(self):
        """Test that different arguments don't use same cache"""
        call_count = 0
        
        @cached(ttl_seconds=60)
        def expensive_function(x):
            nonlocal call_count
            call_count += 1
            return x * 2
        
        result1 = expensive_function(5)
        result2 = expensive_function(10)
        
        assert result1 == 10
        assert result2 == 20
        assert call_count == 2  # Called twice
    
    def test_clear_cache_global(self):
        """Test global cache clearing"""
        call_count = 0
        
        @cached(ttl_seconds=60)
        def expensive_function(x):
            nonlocal call_count
            call_count += 1
            return x * 2
        
        expensive_function(5)
        clear_cache()
        expensive_function(5)  # Should call again after clear
        
        assert call_count == 2
    
    def test_invalidate_cache_pattern(self):
        """Test pattern-based invalidation using direct cache manipulation"""
        from modules.cache import _global_cache
        
        # Manually add cache entries with known keys
        _global_cache.set("user_123_data", {"id": 123, "name": "User 123"})
        _global_cache.set("user_456_data", {"id": 456, "name": "User 456"})
        _global_cache.set("product_789", {"id": 789, "name": "Product 789"})
        
        # Invalidate pattern
        invalidate_cache("user_")
        
        # User entries should be gone
        assert _global_cache.get("user_123_data") is None
        assert _global_cache.get("user_456_data") is None
        # Product should remain
        assert _global_cache.get("product_789") is not None
