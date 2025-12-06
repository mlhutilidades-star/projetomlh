#!/usr/bin/env python3
"""
Testar variações de ENDPOINTS para Shopee
Talvez o path esteja errado
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

endpoints_to_test = [
    # Possíveis endpoints para PRODUTOS
    "https://partner.shopeemobile.com/api/v2/product/get_item_list",
    "https://partner.shopeemobile.com/api/v2/product/get_items",
    "https://partner.shopeemobile.com/api/v2/product/list",
    "https://partner.shopeemobile.com/api/v2/products",
    "https://partner.shopeemobile.com/api/v1/product/get_item_list",
    
    # Open Platform diferente
    "https://open-api.shopee.com/v2/product/get_item_list",
    "https://open-api.shopee.com/v2/product/list",
    
    # Possíveis para PEDIDOS  
    "https://partner.shopeemobile.com/api/v2/order/get_order_list",
    "https://partner.shopeemobile.com/api/v2/order/list",
    "https://partner.shopeemobile.com/api/v2/orders",
    
    # SHOP info
    "https://partner.shopeemobile.com/api/v2/shop/get_shop_info",
    
]

print("\n" + "="*80)
print("🔍 TESTANDO ENDPOINTS CORRETOS PARA SHOPEE")
print("="*80)

for endpoint_url in endpoints_to_test:
    try:
        # Simples GET sem autenticação para ver se endpoint existe
        response = requests.get(endpoint_url, timeout=3)
        status = response.status_code
        
        try:
            body = response.json()
            error = body.get("error", "")
            message = body.get("message", "")[:50]
        except:
            error = ""
            message = response.text[:50]
        
        endpoint_path = endpoint_url.replace("https://partner.shopeemobile.com/api/v2", "").replace("https://open-api.shopee.com/v2", "")
        
        if status != 404:
            print(f"\n✅ {endpoint_path}")
            print(f"   Status: {status} | Error: {error} | {message}")
        else:
            print(f"❌ {endpoint_path}")
    
    except Exception as e:
        print(f"⚠️  {endpoint_url}: {str(e)[:40]}")

print("\n" + "="*80)
