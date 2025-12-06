#!/usr/bin/env python3
"""
Testar diferentes endpoints para ver qual funciona
"""
import requests
import hmac
import hashlib
import time

PARTNER_ID = "2013808"
PARTNER_KEY = "shpk4774635844546f67744c5150584a6e554b454f4a576c514b65734c664952"
ACCESS_TOKEN = "624d57696477734248724d474444e4676"
SHOP_ID = "1616902621"

BASE_URL = "https://partner.shopeemobile.com/api/v2"
TIMESTAMP = int(time.time())

def sign_request(path):
    """Assinar requisição"""
    base_string = f"{PARTNER_ID}{path}{TIMESTAMP}"
    signature = hmac.new(
        PARTNER_KEY.encode(),
        base_string.encode(),
        hashlib.sha256
    ).hexdigest()
    return signature

endpoints_to_test = [
    "/shop/get_shop_info",
    "/product/get_item_list",
    "/order/get_order_list",
    "/discount/get_discount_by_item_list",
    "/logistics/get_shipping_parameter",
    "/payment/transaction_list",
    "/public/ping",
]

print("="*70)
print("🔬 TESTAR DIFERENTES ENDPOINTS")
print("="*70)

for endpoint in endpoints_to_test:
    signature = sign_request(endpoint)
    url = f"{BASE_URL}{endpoint}"
    
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
            message = data.get("message", "")
            
            if error == "error_sign":
                result = "❌ WRONG SIGN"
            elif error == "error_not_found":
                result = "❌ NOT FOUND (endpoint não existe)"
            elif error == "error_param":
                result = "⚠️  PARAM ERROR (signature OK, faltam params)"
            elif error == "":
                result = "✅ OK"
            else:
                result = f"❓ {error}"
            
            print(f"\n{endpoint}")
            print(f"  Status: {response.status_code}")
            print(f"  Resultado: {result}")
            if error != "":
                print(f"  Mensagem: {message}")
            
        except:
            print(f"\n{endpoint}")
            print(f"  Status: {response.status_code}")
            print(f"  Response: {response.text[:100]}")
    
    except Exception as e:
        print(f"\n{endpoint}")
        print(f"  ❌ Erro: {str(e)[:50]}")
    
    time.sleep(0.5)

print("\n" + "="*70)
print("💡 ANALISANDO RESULTADOS")
print("="*70)
print("""
Se vir:
- ❌ WRONG SIGN em TODOS: Problema é a chave ou fórmula
- ✅ OK em algum: Esse endpoint funciona, use como base
- ⚠️  PARAM ERROR: Signature está OK! Só faltam parâmetros
- ❌ NOT FOUND: Endpoint não existe ou não tem acesso
""")
