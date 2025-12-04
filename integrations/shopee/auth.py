# integrations/shopee/auth.py
import os
import time
import hmac
import hashlib
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class ShopeeAuth:
    def __init__(self):
        self.partner_id = int(os.getenv('SHOPEE_PARTNER_ID'))
        self.partner_key = os.getenv('SHOPEE_PARTNER_KEY')
        self.shop_id = int(os.getenv('SHOPEE_SHOP_ID'))
        if not all([self.partner_id, self.partner_key, self.shop_id]):
            raise ValueError("Credenciais da Shopee não definidas.")

    def get_auth_params(self, path: str) -> dict:
        timestamp = int(time.time())
        base_string = f"{self.partner_id}{path}{timestamp}"
        sign = hmac.new(self.partner_key.encode('utf-8'), base_string.encode('utf-8'), hashlib.sha256).hexdigest()
        return {"partner_id": self.partner_id, "shop_id": self.shop_id, "timestamp": timestamp, "sign": sign}
