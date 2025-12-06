#!/usr/bin/env python3
"""
Testar se a fórmula EXATA de /auth/token/get funciona para /product/get_item_list
"""
import requests
import hmac
import hashlib
import time

PARTNER_ID = "2013808"
PARTNER_KEY = "shpk4774635844546f67744c5150584a6e554b454f4a576c514b65734c664952"
ACCESS_TOKEN = "54666a41686a75534a61527167454353"
SHOP_ID = "1616902621"
SHOPEE_API = "https://partner.shopeemobile.com/api/v2"

def generate_sign(path: str, timestamp: int) -> str:
    """Fórmula EXATA que funcionou para /auth/token/get"""
    base_string = f"{PARTNER_ID}{path}{timestamp}"
    return hmac.new(
        PARTNER_KEY.encode(),
        base_string.encode(),
        hashlib.sha256
    ).hexdigest()

print("\n" + "="*80)
print("🔍 TESTANDO COM FÓRMULA CORRETA: {partner_id}{path}{timestamp}")
print("="*80)

paths = [
    "/product/get_item_list",
    "/order/get_order_list",
    "/shop/get_shop_info",
]

for path in paths:
    print(f"\n\n🔗 Path: {path}")
    print("-" * 80)
    
    timestamp = int(time.time())
    sign = generate_sign(path, timestamp)
    
    params = {
        "partner_id": PARTNER_ID,
        "timestamp": timestamp,
        "sign": sign,
        "shop_id": SHOP_ID,
        "access_token": ACCESS_TOKEN,  # Adicionar sempre
    }
    
    print(f"Timestamp: {timestamp}")
    print(f"Sign: {sign}")
    print(f"Params: partner_id, shop_id, timestamp, sign, access_token")
    
    try:
        response = requests.get(
            f"{SHOPEE_API}{path}",
            params=params,
            timeout=5
        )
        
        result = response.json()
        status = response.status_code
        error = result.get("error", "")
        message = result.get("message", "")[:80]
        
        print(f"\nStatus: {status}")
        print(f"Error: {error}")
        print(f"Message: {message}")
        
        # Verificar se funcionou
        if status == 200 and not error:
            print(f"\n✅ FUNCIONOU COM ESSE PATH!")
            print(f"Response: {result}")
            break
        elif status == 200 and error == "error_sign":
            print(f"❌ Ainda 'wrong sign'")
        else:
            print(f"⚠️  Outro erro")
    
    except Exception as e:
        print(f"Erro: {e}")

print("\n" + "="*80)
