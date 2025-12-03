import requests
from typing import Dict, List

def importar_vendas_shopee(api_token: str, shop_id: int) -> List[Dict]:
    """
    Importa vendas/pedidos da Shopee.

    :param api_token: Token de autenticação da API Shopee.
    :param shop_id: ID da loja na Shopee.
    :return: Lista de dicionários com os dados dos pedidos.
    """
    url = f"https://partner.shopeemobile.com/api/v2/order/get_order_list"
    headers = {
        "Content-Type": "application/json"
    }
    payload = {
        "access_token": api_token,
        "shop_id": shop_id,
        "time_range_field": "create_time",
        "time_from": 0,
        "time_to": 9999999999,
        "page_size": 100,
        "page_no": 1
    }

    response = requests.post(url, json=payload, headers=headers)
    return response.json().get('orders', [])
