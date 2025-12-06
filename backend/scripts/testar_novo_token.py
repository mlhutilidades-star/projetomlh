#!/usr/bin/env python3
"""
Testar novo access token
"""
import requests
import hmac
import hashlib
import time

PARTNER_ID = "2013808"
PARTNER_KEY = "shpk4774635844546f67744c5150584a6e554b454f4a576c514b65734c664952"
ACCESS_TOKEN = "4f437355766f646b4f7370527a6e6f49"
SHOP_ID = "1616902621"

def generate_sign(path, timestamp):
    base_string = f"{PARTNER_ID}{path}{timestamp}"
    return hmac.new(
        PARTNER_KEY.encode(),
        base_string.encode(),
        hashlib.sha256
    ).hexdigest()

print("="*70)
print("🧪 TESTANDO NOVO ACCESS TOKEN")
print("="*70)

path = "/api/v2/product/get_item_list"
timestamp = int(time.time())
sign = generate_sign(path, timestamp)

url = f"https://partner.shopeemobile.com{path}"
params = {
    "access_token": ACCESS_TOKEN,
    "partner_id": PARTNER_ID,
    "shop_id": SHOP_ID,
    "timestamp": timestamp,
    "sign": sign,
    "page_size": 10,
    "offset": 0
}

print(f"\n📡 Chamando API: GET {path}")
print(f"Timestamp: {timestamp}")
print(f"Sign: {sign[:32]}...")

response = requests.get(url, params=params)

print(f"\n📥 Resposta:")
print(f"Status: {response.status_code}")

data = response.json()
if "error" in data and data["error"]:
    print(f"❌ Erro: {data['error']}")
    print(f"Mensagem: {data.get('message', 'N/A')}")
else:
    print(f"✅ SUCESSO! Token está válido!")
    if "response" in data and "item" in data["response"]:
        items = data["response"]["item"]
        print(f"\n📦 Total de produtos: {data['response'].get('total_count', len(items))}")
        if items:
            print(f"\nPrimeiro produto:")
            print(f"  - Item ID: {items[0].get('item_id')}")
            print(f"  - Nome: {items[0].get('item_name', 'N/A')}")
