import requests
from typing import Dict, List

def sincronizar_estoque(api_token: str, dados_estoque: List[Dict]) -> Dict:
    """
    Sincroniza dados de estoque com a API Tiny.

    :param api_token: Token de autenticação da API Tiny.
    :param dados_estoque: Lista de dicionários com os dados de estoque a serem sincronizados.
    :return: Dicionário com a resposta da API.
    """
    url = "https://api.tiny.com.br/api2/produto.alterarEstoque"
    headers = {
        "Content-Type": "application/json"
    }
    payload = {
        "token": api_token,
        "dados": dados_estoque
    }

    response = requests.post(url, json=payload, headers=headers)
    return response.json()
