#!/usr/bin/env python3
"""
Testar hipóteses alternativas de assinatura
"""
import requests
import hmac
import hashlib
import time

PARTNER_ID = "2013808"
API_KEY = "shpk4774635844546f67744c5150584a6e554b454f4a576c514b65734c664952"
ACCESS_TOKEN = "624d57696477734248724d474444e4676"
SHOP_ID = "1616902621"
PATH = "/product/get_item_list"

print("="*70)
print("🔬 TESTE DAS HIPÓTESES ALTERNATIVAS")
print("="*70)

# TESTE 1: Access token no HEADER
print("\n\n📝 TESTE 1: Access Token no HEADER (não params)")
print("="*70)

TIMESTAMP = int(time.time())
base_string = f"{PARTNER_ID}{PATH}{TIMESTAMP}"
sig = hmac.new(API_KEY.encode(), base_string.encode(), hashlib.sha256).hexdigest()

url = f"https://partner.shopeemobile.com/api/v2{PATH}"

params = {
    "partner_id": PARTNER_ID,
    "shop_id": SHOP_ID,
    "timestamp": TIMESTAMP,
    "sign": sig
}

headers = {
    "X-Shopee-Access-Token": ACCESS_TOKEN,
    "Content-Type": "application/json"
}

try:
    r = requests.get(url, params=params, headers=headers, timeout=10)
    data = r.json()
    error = data.get("error", "")
    print(f"Status: {r.status_code}")
    print(f"Error: {error if error else '✅ OK'}")
    if error:
        print(f"Message: {data.get('message', '')}")
except Exception as e:
    print(f"Erro: {e}")

# TESTE 2: Timestamp em milissegundos
print("\n\n📝 TESTE 2: Timestamp em MILISSEGUNDOS")
print("="*70)

TIMESTAMP_MS = int(time.time() * 1000)
base_string = f"{PARTNER_ID}{PATH}{TIMESTAMP_MS}"
sig = hmac.new(API_KEY.encode(), base_string.encode(), hashlib.sha256).hexdigest()

params = {
    "partner_id": PARTNER_ID,
    "shop_id": SHOP_ID,
    "access_token": ACCESS_TOKEN,
    "timestamp": TIMESTAMP_MS,
    "sign": sig
}

try:
    r = requests.get(url, params=params, timeout=10)
    data = r.json()
    error = data.get("error", "")
    print(f"Status: {r.status_code}")
    print(f"Error: {error if error else '✅ OK'}")
    if error:
        print(f"Message: {data.get('message', '')}")
except Exception as e:
    print(f"Erro: {e}")

# TESTE 3: SEM partner_id na assinatura
print("\n\n📝 TESTE 3: SEM partner_id na ASSINATURA")
print("="*70)

TIMESTAMP = int(time.time())
base_string = f"{PATH}{SHOP_ID}{TIMESTAMP}"  # SEM partner_id
sig = hmac.new(API_KEY.encode(), base_string.encode(), hashlib.sha256).hexdigest()

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
    print(f"Error: {error if error else '✅ OK'}")
    if error:
        print(f"Message: {data.get('message', '')}")
except Exception as e:
    print(f"Erro: {e}")

# TESTE 4: path + timestamp APENAS
print("\n\n📝 TESTE 4: path + timestamp APENAS")
print("="*70)

TIMESTAMP = int(time.time())
base_string = f"{PATH}{TIMESTAMP}"
sig = hmac.new(API_KEY.encode(), base_string.encode(), hashlib.sha256).hexdigest()

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
    print(f"Error: {error if error else '✅ OK'}")
    if error:
        print(f"Message: {data.get('message', '')}")
except Exception as e:
    print(f"Erro: {e}")

# TESTE 5: Sem nenhuma assinatura (só ver se falha diferente)
print("\n\n📝 TESTE 5: SEM ASSINATURA (controle)")
print("="*70)

params = {
    "partner_id": PARTNER_ID,
    "shop_id": SHOP_ID,
    "access_token": ACCESS_TOKEN,
    "timestamp": int(time.time()),
}

try:
    r = requests.get(url, params=params, timeout=10)
    data = r.json()
    error = data.get("error", "")
    print(f"Status: {r.status_code}")
    print(f"Error: {error}")
    print(f"Message: {data.get('message', '')}")
except Exception as e:
    print(f"Erro: {e}")

print("\n" + "="*70)
