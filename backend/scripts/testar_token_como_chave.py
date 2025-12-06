#!/usr/bin/env python3
"""
Testar assinatura com ACCESS_TOKEN como chave de assinatura
(em vez de PARTNER_KEY)
"""
import requests
import hmac
import hashlib
import time

PARTNER_ID = "2013808"
ACCESS_TOKEN = "624d57696477734248724d474444e4676"
SHOP_ID = "1616902621"

PATH = "/product/get_item_list"
TIMESTAMP = int(time.time())

print("="*70)
print("🔬 TESTAR ASSINANDO COM ACCESS_TOKEN (NÃO PARTNER_KEY)")
print("="*70)
print(f"Access Token como CHAVE de assinatura: {ACCESS_TOKEN}")

# Testar se access_token pode ser a chave de assinatura
formulas = {
    "1 - partner+path+time (chave=token)": (f"{PARTNER_ID}{PATH}{TIMESTAMP}", ACCESS_TOKEN),
    "2 - path+shop+time (chave=token)": (f"{PATH}{SHOP_ID}{TIMESTAMP}", ACCESS_TOKEN),
    "3 - shop+path+time (chave=token)": (f"{SHOP_ID}{PATH}{TIMESTAMP}", ACCESS_TOKEN),
    "4 - partner+path+shop+time (chave=token)": (f"{PARTNER_ID}{PATH}{SHOP_ID}{TIMESTAMP}", ACCESS_TOKEN),
}

for name, (base_string, signing_key) in formulas.items():
    signature = hmac.new(
        signing_key.encode(),
        base_string.encode(),
        hashlib.sha256
    ).hexdigest()
    
    url = f"https://partner.shopeemobile.com/api/v2{PATH}"
    
    params = {
        "partner_id": PARTNER_ID,
        "shop_id": SHOP_ID,
        "access_token": ACCESS_TOKEN,
        "timestamp": TIMESTAMP,
        "sign": signature
    }
    
    try:
        response = requests.get(url, params=params, timeout=10)
        
        try:
            data = response.json()
            error = data.get("error", "")
            
            if error == "error_sign":
                result = "❌ WRONG SIGN"
            elif error == "":
                result = "✅ OK!"
            else:
                result = f"⚠️  {error}"
            
            print(f"\n{name}")
            print(f"  {result}")
            
        except:
            print(f"\n{name}")
            print(f"  Status: {response.status_code}")
    
    except Exception as e:
        print(f"\n{name}")
        print(f"  ❌ Erro: {str(e)[:50]}")
    
    time.sleep(0.5)

print("\n" + "="*70)
