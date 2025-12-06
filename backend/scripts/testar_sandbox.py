#!/usr/bin/env python3
"""
Testar endpoints diferentes - Sandbox vs Live
"""
import requests
import hmac
import hashlib
import time

PARTNER_ID = "2013808"
API_KEY = "shpk4774635844546f67744c5150584a6e554b454f4a576c514b65734c664952"
ACCESS_TOKEN = "624d57696477734248724d474444e4676"
SHOP_ID = "1616902621"

# Diferentes base URLs
urls = [
    ("LIVE", "https://partner.shopeemobile.com/api/v2"),
    ("SANDBOX", "https://partner-test.shopeemobile.com/api/v2"),
]

PATH = "/product/get_item_list"
TIMESTAMP = int(time.time())

base_string = f"{PARTNER_ID}{PATH}{TIMESTAMP}"
sig = hmac.new(
    API_KEY.encode('utf-8'),
    base_string.encode('utf-8'),
    hashlib.sha256
).hexdigest()

print("="*70)
print("🔬 TESTAR LIVE vs SANDBOX")
print("="*70)

params = {
    "partner_id": PARTNER_ID,
    "shop_id": SHOP_ID,
    "access_token": ACCESS_TOKEN,
    "timestamp": TIMESTAMP,
    "sign": sig
}

for env_name, base_url in urls:
    print(f"\n📝 {env_name}:")
    url = f"{base_url}{PATH}"
    
    try:
        r = requests.get(url, params=params, timeout=10)
        data = r.json()
        
        error = data.get("error", "")
        message = data.get("message", "")
        
        print(f"   Status: {r.status_code}")
        print(f"   Error: {error if error else '✅ OK'}")
        print(f"   Message: {message}")
        
    except requests.exceptions.ConnectionError:
        print(f"   ❌ Não conseguiu conectar (sandbox pode não existir)")
    except Exception as e:
        print(f"   ❌ Erro: {e}")

print("\n" + "="*70)
