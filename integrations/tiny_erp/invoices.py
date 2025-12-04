# integrations/tiny_erp/invoices.py
import requests
import logging
from integrations.tiny_erp.auth import TinyERPAuth

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class TinyERPInvoiceFetcher:
    def __init__(self, auth_client: TinyERPAuth):
        self.auth_client = auth_client
        self.base_url = "https://api.tiny.com.br/api2"

    def search_purchase_invoices(self, start_date: str, end_date: str) -> list:
        access_token = self.auth_client.get_access_token()
        params = {"token": access_token, "formato": "json", "pesquisa": f"data_emissao[{start_date} TO {end_date}] tipo_nota[E]"}
        endpoint = f"{self.base_url}/notas.fiscais.pesquisa.php"
        try:
            response = requests.get(endpoint, params=params)
            response.raise_for_status()
            data = response.json()
            if data.get('retorno', {}).get('status') == 'OK':
                return data['retorno'].get('notas_fiscais', [])
            else:
                logging.error(f"Erro da API do Tiny ao buscar notas fiscais: {data.get('retorno', {}).get('erros')}")
                return []
        except requests.exceptions.RequestException as e:
            logging.error(f"Erro de conexão ao buscar notas fiscais no Tiny ERP: {e}")
            raise ConnectionError(f"Falha na comunicação com a API do Tiny ERP.")
