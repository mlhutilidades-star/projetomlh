"""
Exemplo de Integração de Cache com Shopee API - Phase 10.
Demonstra como usar cache_wrapper com as APIs existentes.
"""

from modules.cache_wrapper import cached_api_call, CachedAPI
from modules.metrics import measure_performance
import json


class CachedShopeeAPI(CachedAPI):
    """Wrapper de Shopee API com suporte a cache."""
    
    cache_prefix = "shopee_"
    cache_ttl = 3600  # 1 hora
    
    def __init__(self):
        super().__init__()
        self.api_initialized = False
    
    @measure_performance()
    def get_orders(self, shop_id, start_date=None, end_date=None):
        """
        Recupera pedidos da Shopee com cache.
        
        Args:
            shop_id (int): ID da loja Shopee.
            start_date (str): Data inicial (YYYY-MM-DD).
            end_date (str): Data final (YYYY-MM-DD).
        
        Returns:
            list: Lista de pedidos.
        """
        # Tenta recuperar do cache
        cached = self.get_cached(shop_id, start_date, end_date)
        if cached is not None:
            return cached
        
        # TODO: Implementar chamada real à API Shopee
        # Por enquanto, retorna dados simulados
        result = {
            "shop_id": shop_id,
            "orders": [
                {"order_id": 1, "status": "completed", "total": 100},
                {"order_id": 2, "status": "cancelled", "total": 50}
            ],
            "count": 2
        }
        
        # Armazena em cache
        self.set_cached(result, shop_id, start_date, end_date)
        return result
    
    @measure_performance()
    def get_products(self, shop_id, limit=100):
        """
        Recupera produtos da Shopee com cache.
        
        Args:
            shop_id (int): ID da loja Shopee.
            limit (int): Limite de produtos a recuperar.
        
        Returns:
            list: Lista de produtos.
        """
        # Tenta recuperar do cache
        cached = self.get_cached(shop_id, limit)
        if cached is not None:
            return cached
        
        # TODO: Implementar chamada real à API Shopee
        # Por enquanto, retorna dados simulados
        result = {
            "shop_id": shop_id,
            "products": [
                {"product_id": i, "name": f"Produto {i}", "price": 100 + i}
                for i in range(min(limit, 10))
            ],
            "total": min(limit, 10)
        }
        
        # Armazena em cache
        self.set_cached(result, shop_id, limit)
        return result
    
    @measure_performance()
    def get_shop_info(self, shop_id):
        """
        Recupera informações da loja com cache longo.
        
        Args:
            shop_id (int): ID da loja Shopee.
        
        Returns:
            dict: Informações da loja.
        """
        # Cache de 24 horas para info estática
        cached = self.get_cached(shop_id)
        if cached is not None:
            return cached
        
        # TODO: Implementar chamada real à API Shopee
        result = {
            "shop_id": shop_id,
            "shop_name": f"Loja {shop_id}",
            "rating": 4.5,
            "follower_count": 1000
        }
        
        self.set_cached(result, shop_id)
        return result


# Exemplo de uso com decorator
@cached_api_call(ttl=1800, key_prefix="orders_")
def fetch_orders_cached(shop_id: int):
    """
    Exemplo de função com cache de 30 minutos.
    
    Args:
        shop_id (int): ID da loja.
    
    Returns:
        dict: Pedidos da loja.
    """
    # Simulação de chamada cara
    return {
        "shop_id": shop_id,
        "orders": [
            {"id": 1, "amount": 100},
            {"id": 2, "amount": 200}
        ]
    }


def example_usage():
    """Exemplo de uso da API com cache."""
    
    # Criar instância da API com cache
    api = CachedShopeeAPI()
    
    print("=== Exemplo de Integração de Cache com Shopee API ===\n")
    
    # Primeira chamada - sem cache
    print("1️⃣  Primeira chamada - sem cache:")
    orders = api.get_orders(12345)
    print(f"   Pedidos recuperados: {orders['count']}")
    
    # Segunda chamada - com cache
    print("\n2️⃣  Segunda chamada - com cache:")
    orders = api.get_orders(12345)
    print(f"   Pedidos recuperados: {orders['count']} (do cache)")
    
    # Chamar função com decorator
    print("\n3️⃣  Usando decorator @cached_api_call:")
    result = fetch_orders_cached(12345)
    print(f"   Resultado: {len(result['orders'])} pedidos")
    
    # Segunda chamada com decorator
    print("\n4️⃣  Segunda chamada com decorator:")
    result = fetch_orders_cached(12345)
    print(f"   Resultado: {len(result['orders'])} pedidos (do cache)")
    
    # Exibir métricas
    print("\n📊 Métricas de Performance:")
    from modules.metrics import get_metrics
    stats = get_metrics()
    print(f"   Cache Hits: {stats['cache']['hits']}")
    print(f"   Cache Misses: {stats['cache']['misses']}")
    print(f"   Hit Rate: {stats['cache']['hit_rate']:.1%}")


if __name__ == "__main__":
    example_usage()
