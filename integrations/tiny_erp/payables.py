# integrations/tiny_erp/payables.py
import requests
import logging
from integrations.tiny_erp.auth import TinyERPAuth

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class TinyERPPayables:
    def __init__(self, auth_client: TinyERPAuth):
        self.auth_client = auth_client
        self.base_url = "https://api.tiny.com.br/api2"

    def create_payable(self, payable_data: dict) -> dict:
        access_token = self.auth_client.get_access_token()
        endpoint = f"{self.base_url}/incluir.conta.pagar.php"
        payload = {"token": access_token, "formato": "json", "conta": f"[{str(payable_data).replace('\'', '\"')}]"}
        try:
            response = requests.post(endpoint, data=payload)
            response.raise_for_status()
            data = response.json()
            if data.get('retorno', {}).get('status') == 'OK':
                logging.info("Conta a pagar criada com sucesso no Tiny ERP.")
                return data['retorno']
            else:
                logging.error(f"Erro da API do Tiny ao criar conta a pagar: {data.get('retorno', {}).get('erros')}")
                return data['retorno']
        except requests.exceptions.RequestException as e:
            logging.error(f"Erro de conexão ao criar conta a pagar no Tiny ERP: {e}")
            raise ConnectionError(f"Falha na comunicação com a API do Tiny ERP.")
