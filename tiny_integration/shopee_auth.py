import requests
from typing import Dict

def autenticar_shopee(client_id: str, client_secret: str) -> Dict:
    """
    Autentica e conecta com a API Shopee usando as credenciais fornecidas.

    :param client_id: ID do cliente para autenticação na API Shopee.
    :param client_secret: Segredo do cliente para autenticação na API Shopee.
    :return: Dicionário com a resposta da API.
    """
    url = "https://partner.shopeemobile.com/api/v2/auth/token/get"
    headers = {
        "Content-Type": "application/json"
    }
    payload = {
        "client_id": client_id,
        "client_secret": client_secret
    }

    response = requests.post(url, json=payload, headers=headers)
    return response.json()
