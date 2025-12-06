#!/usr/bin/env python3
"""
Testar cada fórmula de HMAC contra a API Shopee de verdade
"""
import requests
import hmac
import hashlib
import time

PARTNER_ID = "2013808"
PARTNER_KEY = "shpk4774635844546f67744c5150584a6e554b454f4a576c514b65734c664952"
ACCESS_TOKEN = "54666a41686a75534a61527167454353"
SHOP_ID = "1616902621"
PATH = "/product/get_item_list"
TIMESTAMP = int(time.time())
SHOPEE_API = "https://partner.shopeemobile.com/api/v2"

formulas = {
    "1_partner_path_time": f"{PARTNER_ID}{PATH}{TIMESTAMP}",
    "2_partner_path_shop_time": f"{PARTNER_ID}{PATH}{SHOP_ID}{TIMESTAMP}",
    "4_path_shop_time_token": f"{PATH}{SHOP_ID}{TIMESTAMP}{ACCESS_TOKEN}",
    "5_path_shop_token_time": f"{PATH}{SHOP_ID}{ACCESS_TOKEN}{TIMESTAMP}",
    "6_partner_path_shop_time_token": f"{PARTNER_ID}{PATH}{SHOP_ID}{TIMESTAMP}{ACCESS_TOKEN}",
    "7_partner_path_token_time": f"{PARTNER_ID}{PATH}{ACCESS_TOKEN}{TIMESTAMP}",
    "8_shop_path_token_time": f"{SHOP_ID}{PATH}{ACCESS_TOKEN}{TIMESTAMP}",
    "9_token_path_shop_time": f"{ACCESS_TOKEN}{PATH}{SHOP_ID}{TIMESTAMP}",
}

print("\n" + "="*80)
print("🚀 TESTANDO FÓRMULAS DE HMAC CONTRA A API SHOPEE")
print("="*80)

for name, base_string in formulas.items():
    sign = hmac.new(
        PARTNER_KEY.encode(),
        base_string.encode(),
        hashlib.sha256
    ).hexdigest()
    
    params = {
        "partner_id": PARTNER_ID,
        "timestamp": TIMESTAMP,
        "sign": sign,
        "shop_id": SHOP_ID,
        "access_token": ACCESS_TOKEN,
    }
    
    try:
        response = requests.get(
            f"{SHOPEE_API}{PATH}",
            params=params,
            timeout=5
        )
        
        result = response.json()
        
        # Verificar se funcionou
        if response.status_code == 200 and "error" not in result:
            print(f"\n✅ FUNCIONOU: {name}")
            print(f"   Base String: {base_string[:60]}...")
            print(f"   Response: {str(result)[:100]}")
            print("\n🎉 FÓRMULA CORRETA ENCONTRADA!")
            break
        elif response.status_code == 200 and result.get("error") == "error_sign":
            print(f"❌ {name}: {result.get('message')}")
        elif response.status_code == 200:
            print(f"⚠️  {name}: {result.get('error')} - {result.get('message')}")
        elif response.status_code == 403:
            error_msg = result.get('message', 'Unknown')
            print(f"🚫 {name}: 403 - {error_msg}")
        else:
            print(f"⚠️  {name}: Status {response.status_code}")
            print(f"   Response: {result}")
    
    except Exception as e:
        print(f"❌ {name}: {str(e)[:50]}")

print("\n" + "="*80)
