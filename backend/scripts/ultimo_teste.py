#!/usr/bin/env python3
"""
Teste FINAL com diferentes possibilidades baseado em padrões de API
"""
import requests
import hmac
import hashlib
import time
from urllib.parse import urlencode, quote

PARTNER_ID = "2013808"
API_KEY_LIVE = "shpk4774635844546f67744c5150584a6e554b454f4a576c514b65734c664952"
ACCESS_TOKEN = "624d57696477734248724d474444e4676"
SHOP_ID = "1616902621"
PATH = "/product/get_item_list"

print("="*70)
print("🔬 ÚLTIMO TESTE - PADRÕES COMUNS DE API")
print("="*70)

TIMESTAMP = int(time.time())

# Diferentes estratégias de assinatura
test_cases = [
    ("Com query string em base", 
     f"{PARTNER_ID}{PATH}?access_token={ACCESS_TOKEN}&shop_id={SHOP_ID}&timestamp={TIMESTAMP}"),
    
    ("Com URL encoded base",
     f"{PARTNER_ID}{PATH}{urlencode({'access_token': ACCESS_TOKEN, 'shop_id': SHOP_ID, 'timestamp': TIMESTAMP})}"),
    
    ("Com separadores de barra",
     f"/api/v2{PATH}/{SHOP_ID}/{TIMESTAMP}"),
    
    ("Com method HTTP",
     f"GET{PATH}{TIMESTAMP}"),
    
    ("Simples timestamp",
     f"{TIMESTAMP}"),
    
    ("Host + path + timestamp",
     f"partner.shopeemobile.com{PATH}{TIMESTAMP}"),
]

url = f"https://partner.shopeemobile.com/api/v2{PATH}"

for test_name, base_string in test_cases:
    sig = hmac.new(
        API_KEY_LIVE.encode('utf-8'),
        base_string.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    
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
            result = "❌"
        elif error == "":
            result = "✅"
        else:
            result = f"⚠️  {error[:20]}"
        
        print(f"{result} {test_name:40} | {data.get('message', '')[:30]}")
        
    except Exception as e:
        print(f"❌ {test_name:40} | Erro: {str(e)[:30]}")
    
    time.sleep(0.3)

print("\n" + "="*70)
print("Se nenhum funcionar, a API pode ter um requisito especial.")
print("Você pode:")
print("1. Procurar no console Shopee por 'API Test Tool'")
print("2. Usar o tool deles para fazer uma requisição de exemplo")
print("3. Copiar exatamente o que ele mostra")
print("="*70)
