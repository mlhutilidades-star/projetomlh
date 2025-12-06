#!/usr/bin/env python3
"""
Testar variações de PATH e se partner_id deve ou não estar na assinatura
"""
import requests
import hmac
import hashlib
import time

PARTNER_ID = "2013808"
PARTNER_KEY = "shpk4774635844546f67744c5150584a6e554b454f4a576c514b65734c664952"
ACCESS_TOKEN = "54666a41686a75534a61527167454353"
SHOP_ID = "1616902621"
TIMESTAMP = int(time.time())
SHOPEE_API = "https://partner.shopeemobile.com/api/v2"

paths_to_test = [
    "/product/get_item_list",
    "product/get_item_list",
    "/v2/product/get_item_list",
    "v2/product/get_item_list",
]

print("\n" + "="*80)
print("🔍 TESTANDO VARIAÇÕES DE PATH")
print("="*80)

for path_test in paths_to_test:
    print(f"\n\n🔗 Testando Path: {path_test}")
    print("-" * 80)
    
    # Formula 1: Sem partner_id (apenas path + access_token + timestamp)
    base_string1 = f"{path_test}{TIMESTAMP}{ACCESS_TOKEN}"
    sign1 = hmac.new(PARTNER_KEY.encode(), base_string1.encode(), hashlib.sha256).hexdigest()
    
    # Formula 2: Com partner_id + path + timestamp
    base_string2 = f"{PARTNER_ID}{path_test}{TIMESTAMP}"
    sign2 = hmac.new(PARTNER_KEY.encode(), base_string2.encode(), hashlib.sha256).hexdigest()
    
    # Testar ambas
    for idx, (sign, base) in enumerate([(sign1, base_string1), (sign2, base_string2)], 1):
        params = {
            "partner_id": PARTNER_ID,
            "timestamp": TIMESTAMP,
            "sign": sign,
            "shop_id": SHOP_ID,
            "access_token": ACCESS_TOKEN,
        }
        
        try:
            response = requests.get(
                f"{SHOPEE_API}{path_test}" if path_test.startswith("/") else f"{SHOPEE_API}/{path_test}",
                params=params,
                timeout=5
            )
            
            result = response.json()
            status = response.status_code
            error_msg = result.get("message", "")[:50] if "message" in result else ""
            
            print(f"  Fórmula {idx}: Status {status} - {error_msg}")
            
            if status == 200 and "error" not in result:
                print(f"    ✅ FUNCIONOU COM PATH: {path_test}")
                print(f"    Sign: {sign[:30]}...")
                
        except Exception as e:
            print(f"  Fórmula {idx}: Erro - {str(e)[:50]}")

print("\n" + "="*80)
