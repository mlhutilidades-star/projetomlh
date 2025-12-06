#!/usr/bin/env python3
"""
Testar com Live API Partner Key encontrada
"""
import requests
import hmac
import hashlib
import time

PARTNER_ID = "2013808"
LIVE_API_KEY = "shpk4774635844546f67744c5150584a6e554b454f4a576c514b65734c664952"
TEST_API_KEY = "shpk6b67764c74556a52584d52476c45576a2c115058da6e554b4554d76c6849"
ACCESS_TOKEN = "624d57696477734248724d474444e4676"
SHOP_ID = "1616902621"

PATH = "/product/get_item_list"
TIMESTAMP = int(time.time())

print("="*70)
print("🔑 TESTAR COM LIVE E TEST API KEYS")
print("="*70)

for key_name, api_key in [("LIVE", LIVE_API_KEY), ("TEST", TEST_API_KEY)]:
    print(f"\n\n📝 Testando com {key_name} API Key:")
    print(f"   {api_key[:40]}...")
    
    base = f"{PARTNER_ID}{PATH}{TIMESTAMP}"
    sig = hmac.new(api_key.encode(), base.encode(), hashlib.sha256).hexdigest()
    
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
        message = data.get("message", "")
        
        print(f"\n   Status: {r.status_code}")
        print(f"   Error: {error if error else '✅ OK (sem erro)'}")
        print(f"   Message: {message}")
        
        if "data" in data and isinstance(data["data"], list):
            print(f"   Items retornados: {len(data['data'])}")
        
        if error == "error_sign":
            print(f"   ❌ WRONG SIGN - Essa chave não funciona")
        elif error == "":
            print(f"   ✅ SUCESSO! Essa chave funciona!")
        else:
            print(f"   ⚠️  Outro erro: {error}")
            
    except Exception as e:
        print(f"   ❌ Erro: {e}")

print("\n" + "="*70)
