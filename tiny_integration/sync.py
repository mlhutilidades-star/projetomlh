import requests
from typing import Dict, List

def sincronizar_dados_financeiros(api_token: str, dados_financeiros: List[Dict]) -> Dict:
    """
    Sincroniza dados financeiros com a API Tiny.

    :param api_token: Token de autenticação da API Tiny.
    :param dados_financeiros: Lista de dicionários com os dados financeiros a serem sincronizados.
    :return: Dicionário com a resposta da API.
    """
    url = "https://api.tiny.com.br/api2/financeiro.incluir"
    headers = {
        "Content-Type": "application/json"
    }
    payload = {
        "token": api_token,
        "dados": dados_financeiros
    }

    response = requests.post(url, json=payload, headers=headers)
    return response.json()
