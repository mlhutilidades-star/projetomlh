#!/usr/bin/env python3
"""
TESTE COM CHAVE DECODIFICADA (HEX)
"""
import requests
import hmac
import hashlib
import time

PARTNER_ID = "2013808"
API_KEY_HEX = "shpk4774635844546f67744c5150584a6e554b454f4a576c514b65734c664952"

# Decodificar a chave (remover prefix shpk e decodificar de hex)
API_KEY_DECODED = bytes.fromhex(API_KEY_HEX[4:]).decode('utf-8')
print(f"🔑 Chave HEX Original: {API_KEY_HEX}")
print(f"🔓 Chave Decodificada: {API_KEY_DECODED}")

ACCESS_TOKEN = "624d57696477734248724d474444e4676"
SHOP_ID = "1616902621"
PATH = "/product/get_item_list"
TIMESTAMP = int(time.time())

print(f"\n📋 Parâmetros:")
print(f"   Partner ID: {PARTNER_ID}")
print(f"   Shop ID: {SHOP_ID}")
print(f"   Path: {PATH}")
print(f"   Timestamp: {TIMESTAMP}")

# Teste 1: Com chave decodificada como string
print(f"\n\n📝 TESTE 1: Chave DECODIFICADA como String")
print("="*70)

base_string = f"{PARTNER_ID}{PATH}{TIMESTAMP}"
sig = hmac.new(
    API_KEY_DECODED.encode('utf-8'),
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

try:
    r = requests.get(url, params=params, timeout=10)
    data = r.json()
    
    error = data.get("error", "")
    print(f"Status: {r.status_code}")
    print(f"Error: {error if error else '✅ SUCESSO'}")
    print(f"Message: {data.get('message', '')}")
    
    if not error and "data" in data:
        items = data.get('data', [])
        print(f"Items retornados: {len(items) if isinstance(items, list) else 'N/A'}")
        
except Exception as e:
    print(f"❌ Erro: {e}")

# Teste 2: Com chave decodificada em bytes
print(f"\n\n📝 TESTE 2: Chave DECODIFICADA como Bytes")
print("="*70)

base_string = f"{PARTNER_ID}{PATH}{TIMESTAMP}"
key_bytes = bytes.fromhex(API_KEY_HEX[4:])
sig = hmac.new(
    key_bytes,
    base_string.encode('utf-8'),
    hashlib.sha256
).hexdigest()

params = {
    "partner_id": PARTNER_ID,
    "shop_id": SHOP_ID,
    "access_token": ACCESS_TOKEN,
    "timestamp": TIMESTAMP,
    "sign": sig
}

try:
    r = requests.get(url, params=params, timeout=10)
    data = r.json()
    
    error = data.get("error", "")
    print(f"Status: {r.status_code}")
    print(f"Error: {error if error else '✅ SUCESSO'}")
    print(f"Message: {data.get('message', '')}")
    
    if not error and "data" in data:
        items = data.get('data', [])
        print(f"Items retornados: {len(items) if isinstance(items, list) else 'N/A'}")
        
except Exception as e:
    print(f"❌ Erro: {e}")

print("\n" + "="*70)
