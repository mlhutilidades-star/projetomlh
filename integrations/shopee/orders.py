# integrations/shopee/orders.py
import os
import requests
import logging
from integrations.shopee.auth import ShopeeAuth
from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class ShopeeOrders:
    def __init__(self, auth_client: ShopeeAuth):
        self.auth_client = auth_client
        self.base_url = "https://partner.shopeemobile.com"

    def get_order_list(self) -> list:
        """
        Busca lista de pedidos da Shopee API v2.
        
        Returns:
            list: Lista de pedidos ou lista vazia em caso de erro
        """
        api_path = "/api/v2/orders/"
        auth_params = self.auth_client.get_auth_params(api_path)
        
        endpoint = f"{self.base_url}{api_path}"
        params = {
            "partner_id": auth_params["partner_id"],
            "shop_id": auth_params["shop_id"],
            "timestamp": auth_params["timestamp"],
            "sign": auth_params["sign"]
        }
        
        try:
            response = requests.get(endpoint, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            if data.get('error') == 0:
                logging.info(f"Pedidos recuperados com sucesso. Total: {len(data.get('response', []))}")
                return data.get('response', [])
            else:
                error_msg = data.get('message', 'Erro desconhecido')
                logging.error(f"Erro ao buscar pedidos: {error_msg}")
                return []
        except requests.exceptions.RequestException as e:
            logging.error(f"Erro de conexão ao buscar pedidos da Shopee: {e}")
            return []
        except Exception as e:
            logging.error(f"Erro inesperado ao buscar pedidos: {e}")
            return []


if __name__ == '__main__':
    load_dotenv()
    
    try:
        # Inicializa autenticação
        auth = ShopeeAuth()
        
        # Cria gerenciador de pedidos
        orders_manager = ShopeeOrders(auth)
        
        # Busca pedidos
        orders = orders_manager.get_order_list()
        
        print("Pedidos encontrados:")
        print(orders)
        
    except ValueError as e:
        print(f"Erro de configuração: {e}")
    except Exception as e:
        print(f"Erro: {e}")
