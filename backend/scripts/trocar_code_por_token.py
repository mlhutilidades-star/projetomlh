#!/usr/bin/env python3
"""
Trocar authorization code por access token
"""
import requests
import hmac
import hashlib
import time

PARTNER_ID = "2013808"
PARTNER_KEY = "shpk4774635844546f67744c5150584a6e554b454f4a576c514b65734c664952"
SHOP_ID = "1616902621"
CODE = "44756b73664b4263745a557074517954"  # Extraído da URL

def generate_sign(path, timestamp):
    base_string = f"{PARTNER_ID}{path}{timestamp}"
    return hmac.new(
        PARTNER_KEY.encode(),
        base_string.encode(),
        hashlib.sha256
    ).hexdigest()

print("="*70)
print("🔄 TROCANDO CODE POR ACCESS TOKEN")
print("="*70)

path = "/api/v2/auth/token/get"
timestamp = int(time.time())
sign = generate_sign(path, timestamp)

url = f"https://partner.shopeemobile.com{path}"
params = {
    "partner_id": PARTNER_ID,
    "timestamp": timestamp,
    "sign": sign
}

body = {
    "code": CODE,
    "shop_id": int(SHOP_ID),
    "partner_id": int(PARTNER_ID)
}

print(f"\n📡 Enviando requisição...")
print(f"URL: {url}")
print(f"Params: {params}")
print(f"Body: {body}")

response = requests.post(url, params=params, json=body)

print(f"\n📥 Resposta:")
print(f"Status: {response.status_code}")
print(f"Body: {response.text}")

if response.status_code == 200:
    data = response.json()
    if "access_token" in data:
        print("\n✅ SUCESSO!")
        print(f"\nACCESS_TOKEN: {data['access_token']}")
        print(f"REFRESH_TOKEN: {data['refresh_token']}")
        print(f"EXPIRE_IN: {data.get('expire_in', 'N/A')} segundos")
        
        print("\n📝 Atualize o .env:")
        print(f'SHOPEE_ACCESS_TOKEN="{data["access_token"]}"')
        print(f'SHOPEE_REFRESH_TOKEN="{data["refresh_token"]}"')
    else:
        print(f"\n❌ Erro: {data}")
else:
    print(f"\n❌ Falha na requisição")
