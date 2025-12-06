#!/usr/bin/env python3
"""
Testar incluindo access_token NA BASE de assinatura
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
TIMESTAMP = int(time.time())

print("="*70)
print("🔬 TESTAR COM ACCESS_TOKEN NA BASE DE ASSINATURA")
print("="*70)

# Diferentes formas de incluir access_token
formulas = [
    ("partner+path+shop+token+time", f"{PARTNER_ID}{PATH}{SHOP_ID}{ACCESS_TOKEN}{TIMESTAMP}"),
    ("partner+path+token+shop+time", f"{PARTNER_ID}{PATH}{ACCESS_TOKEN}{SHOP_ID}{TIMESTAMP}"),
    ("path+shop+token+time", f"{PATH}{SHOP_ID}{ACCESS_TOKEN}{TIMESTAMP}"),
    ("token+partner+path+time", f"{ACCESS_TOKEN}{PARTNER_ID}{PATH}{TIMESTAMP}"),
    ("partner+path+token+time", f"{PARTNER_ID}{PATH}{ACCESS_TOKEN}{TIMESTAMP}"),
    ("partner|path|shop_id|access_token|timestamp", f"{PARTNER_ID}|{PATH}|{SHOP_ID}|{ACCESS_TOKEN}|{TIMESTAMP}"),
]

for name, base_string in formulas:
    sig = hmac.new(API_KEY.encode(), base_string.encode(), hashlib.sha256).hexdigest()
    
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
        
        if error == "error_sign":
            status = "❌"
        elif error == "":
            status = "✅"
        else:
            status = "⚠️"
        
        print(f"\n{status} {name}")
        if error != "error_sign":
            print(f"   Error: {error}")
            
    except Exception as e:
        print(f"\n❌ {name}")
        print(f"   Erro: {str(e)[:40]}")
    
    time.sleep(0.5)

print("\n" + "="*70)
