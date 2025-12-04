# integrations/shopee/products.py
import os
import requests
import logging
from integrations.shopee.auth import ShopeeAuth
from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class ShopeeProducts:
    def __init__(self, auth_client: ShopeeAuth):
        self.auth_client = auth_client
        self.base_url = "https://partner.shopeemobile.com"

    def get_products_list(self, page: int = 1, page_size: int = 100) -> list:
        """
        Busca lista de produtos da loja Shopee.
        
        Args:
            page: Número da página (padrão: 1)
            page_size: Quantidade de itens por página (padrão: 100)
            
        Returns:
            list: Lista de produtos ou lista vazia em caso de erro
        """
        api_path = "/api/v2/product/get_item_list"
        auth_params = self.auth_client.get_auth_params(api_path)
        
        endpoint = f"{self.base_url}{api_path}"
        params = {
            "partner_id": auth_params["partner_id"],
            "shop_id": auth_params["shop_id"],
            "timestamp": auth_params["timestamp"],
            "sign": auth_params["sign"],
            "pagination_entries_per_page": page_size,
            "pagination_offset": (page - 1) * page_size
        }
        
        try:
            response = requests.get(endpoint, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            if data.get('error') == 0:
                items = data.get('response', {}).get('item', [])
                logging.info(f"Produtos recuperados com sucesso. Total: {len(items)}")
                return items
            else:
                error_msg = data.get('message', 'Erro desconhecido')
                logging.error(f"Erro ao buscar produtos: {error_msg}")
                return []
        except requests.exceptions.RequestException as e:
            logging.error(f"Erro de conexão ao buscar produtos da Shopee: {e}")
            return []
        except Exception as e:
            logging.error(f"Erro inesperado ao buscar produtos: {e}")
            return []

    def get_product_details(self, item_id: int) -> dict:
        """
        Busca detalhes de um produto específico.
        
        Args:
            item_id: ID do produto na Shopee
            
        Returns:
            dict: Dados do produto ou dicionário vazio em caso de erro
        """
        api_path = "/api/v2/product/get_item_base_info"
        auth_params = self.auth_client.get_auth_params(api_path)
        
        endpoint = f"{self.base_url}{api_path}"
        params = {
            "partner_id": auth_params["partner_id"],
            "shop_id": auth_params["shop_id"],
            "timestamp": auth_params["timestamp"],
            "sign": auth_params["sign"],
            "item_id": item_id
        }
        
        try:
            response = requests.get(endpoint, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            if data.get('error') == 0:
                product = data.get('response', {})
                logging.info(f"Detalhes do produto {item_id} recuperados com sucesso")
                return product
            else:
                error_msg = data.get('message', 'Erro desconhecido')
                logging.error(f"Erro ao buscar detalhes do produto {item_id}: {error_msg}")
                return {}
        except requests.exceptions.RequestException as e:
            logging.error(f"Erro de conexão ao buscar detalhes do produto: {e}")
            return {}
        except Exception as e:
            logging.error(f"Erro inesperado ao buscar detalhes do produto: {e}")
            return {}


if __name__ == '__main__':
    load_dotenv()
    
    try:
        # Inicializa autenticação
        auth = ShopeeAuth()
        
        # Cria gerenciador de produtos
        products_manager = ShopeeProducts(auth)
        
        # Busca lista de produtos
        products = products_manager.get_products_list()
        print(f"Produtos encontrados: {len(products)}")
        print(products)
        
    except ValueError as e:
        print(f"Erro de configuração: {e}")
    except Exception as e:
        print(f"Erro: {e}")
