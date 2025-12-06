#!/usr/bin/env python3
"""
Monitorar logs do ngrok para capturar callback instantaneamente
"""
import requests
import hmac
import hashlib
import time
import webbrowser
from urllib.parse import parse_qs, urlparse

PARTNER_ID = "2013808"
PARTNER_KEY = "shpk4774635844546f67744c5150584a6e554b454f4a576c514b65734c664952"
SHOP_ID = "1616902621"
REDIRECT_URL = "https://lynette-semiexpositive-broadly.ngrok-free.dev/callback"

def generate_sign(path, timestamp):
    base_string = f"{PARTNER_ID}{path}{timestamp}"
    return hmac.new(
        PARTNER_KEY.encode(),
        base_string.encode(),
        hashlib.sha256
    ).hexdigest()

def exchange_code_for_token(code):
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
        "code": code,
        "shop_id": int(SHOP_ID),
        "partner_id": int(PARTNER_ID)
    }
    
    response = requests.post(url, params=params, json=body, timeout=10)
    return response

print("="*70)
print("🔐 TROCA INSTANTÂNEA DE TOKEN")
print("="*70)

# Cole a URL completa do callback
print("\n📋 Cole a URL completa do callback (com o code):")
callback_url = input("> ").strip()

# Extrair code da URL
parsed = urlparse(callback_url)
params = parse_qs(parsed.query)

if 'code' not in params:
    print("❌ Code não encontrado na URL!")
    exit(1)

code = params['code'][0]
print(f"\n✅ Code extraído: {code}")
print(f"\n🔄 Trocando por access token...")

response = exchange_code_for_token(code)

print(f"\n📥 Resposta:")
print(f"Status: {response.status_code}")

if response.status_code == 200:
    data = response.json()
    if "access_token" in data:
        print(f"\n✅ SUCESSO!")
        print(f"\nACCESS_TOKEN: {data['access_token']}")
        print(f"REFRESH_TOKEN: {data['refresh_token']}")
        print(f"EXPIRE_IN: {data.get('expire_in', 'N/A')} segundos")
        
        print(f"\n📝 Copie para o .env:")
        print(f'SHOPEE_ACCESS_TOKEN="{data["access_token"]}"')
        print(f'SHOPEE_REFRESH_TOKEN="{data["refresh_token"]}"')
    else:
        print(f"\n❌ Erro: {data}")
else:
    print(f"Body: {response.text}")
    print(f"\n❌ Falha")
