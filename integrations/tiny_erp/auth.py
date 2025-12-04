# integrations/tiny_erp/auth.py
import os
import requests
import logging
from datetime import datetime, timedelta

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class TinyERPAuth:
    def __init__(self):
        self.token = os.getenv('TINY_API_TOKEN')
        if not self.token:
            raise ValueError("A variável de ambiente 'TINY_API_TOKEN' não foi definida.")
        self.base_url = "https://api.tiny.com.br"
        self._access_token = None
        self._token_expiry_time = None

    def get_access_token(self) -> str:
        if self._is_token_expired():
            logging.info("Token de acesso expirado ou inexistente. Solicitando um novo...")
            self._request_new_token()
        return self._access_token

    def _is_token_expired(self) -> bool:
        if not self._access_token or not self._token_expiry_time:
            return True
        return datetime.now() >= (self._token_expiry_time - timedelta(minutes=5))

    def _request_new_token(self):
        logging.info("Simulando obtenção de token de acesso. Em um cenário real, aqui ocorreria a chamada OAuth2.")
        response_data = {"access_token": self.token, "expires_in": 3600}
        if response_data.get("access_token"):
            self._access_token = response_data["access_token"]
            expires_in = response_data.get("expires_in", 3600)
            self._token_expiry_time = datetime.now() + timedelta(seconds=expires_in)
            logging.info(f"Novo token de acesso obtido. Válido até: {self._token_expiry_time.strftime('%Y-%m-%d %H:%M:%S')}")
        else:
            logging.error("Falha ao obter o token de acesso do Tiny ERP.")
            raise ConnectionError("Não foi possível autenticar com a API do Tiny ERP.")
