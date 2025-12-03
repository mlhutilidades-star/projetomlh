import requests
from typing import Dict

def autenticar_tiny(api_token: str) -> Dict:
    """
    Autentica e conecta com a API Tiny usando o token fornecido.

    :param api_token: Token de autenticação da API Tiny.
    :return: Dicionário com a resposta da API.
    """
    url = "https://api.tiny.com.br/api2/token"
    headers = {
        "Content-Type": "application/json"
    }
    payload = {
        "token": api_token
    }

    response = requests.post(url, json=payload, headers=headers)
    return response.json()
