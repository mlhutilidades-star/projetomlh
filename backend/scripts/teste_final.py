#!/usr/bin/env python3
"""
Teste FINAL com timestamp correto
"""
import requests
import hmac
import hashlib
import time

PARTNER_ID = "2013808"
API_KEY_LIVE = "shpk4774635844546f67744c5150584a6e554b454f4a576c514b65734c664952"
ACCESS_TOKEN = "624d57696477734248724d474444e4676"
SHOP_ID = "1616902621"
PATH = "/product/get_item_list"

print("="*70)
print("✅ TESTE FINAL - SHOPEE SYNC")
print("="*70)

TIMESTAMP = int(time.time())
base_string = f"{PARTNER_ID}{PATH}{TIMESTAMP}"
sig = hmac.new(
    API_KEY_LIVE.encode('utf-8'),
    base_string.encode('utf-8'),
    hashlib.sha256
).hexdigest()

url = f"https://partner.shopeemobile.com/api/v2{PATH}"

params = {
    "partner_id": PARTNER_ID,
    "shop_id": SHOP_ID,
    "access_token": ACCESS_TOKEN,
    "timestamp": TIMESTAMP,
    "sign": sig
}

print(f"\n📋 Requisição:")
print(f"   URL: {url}")
print(f"   Partner ID: {PARTNER_ID}")
print(f"   Shop ID: {SHOP_ID}")
print(f"   Access Token: {ACCESS_TOKEN[:20]}...")
print(f"   Timestamp: {TIMESTAMP}")
print(f"   Signature: {sig[:40]}...")

print(f"\n📤 Enviando...")

try:
    r = requests.get(url, params=params, timeout=10)
    data = r.json()
    
    print(f"\n📥 Resposta:")
    print(f"   Status: {r.status_code}")
    
    error = data.get("error", "")
    message = data.get("message", "")
    
    if error:
        print(f"   Error: {error}")
        print(f"   Message: {message}")
    else:
        print(f"   ✅ SUCESSO!")
        print(f"   Message: {message}")
    
    # Se houver dados, mostrar
    if "data" in data:
        if isinstance(data["data"], list):
            print(f"   Items: {len(data['data'])}")
            if data["data"]:
                print(f"   Primeiro item: {str(data['data'][0])[:100]}...")
        else:
            print(f"   Data: {str(data['data'])[:200]}...")
    
    # Mostrar response completo se for sucesso
    if not error:
        import json
        print(f"\n📊 Response Completo:")
        print(json.dumps(data, indent=2)[:500])
        
except Exception as e:
    print(f"   ❌ Erro: {e}")

print("\n" + "="*70)
