#!/usr/bin/env python3
"""
Debug profundo - verificar a chave e a assinatura
"""
import hmac
import hashlib

PARTNER_ID = "2013808"
API_KEY_LIVE = "shpk4774635844546f67744c5150584a6e554b454f4a576c514b65734c664952"
API_KEY_TEST = "shpk6b67764c74556a52584d52476c45576a2c115058da6e554b4554d76c6849"
PATH = "/product/get_item_list"
TIMESTAMP = "1764972000"  # Timestamp fixo para testes

print("="*70)
print("🔍 DEBUG - Analisando Chaves e Assinaturas")
print("="*70)

print(f"\n📝 LIVE API Key:")
print(f"   Valor: {API_KEY_LIVE}")
print(f"   Comprimento: {len(API_KEY_LIVE)}")
print(f"   Começa com: {API_KEY_LIVE[:20]}")
print(f"   Termina com: {API_KEY_LIVE[-20:]}")

print(f"\n📝 TEST API Key:")
print(f"   Valor: {API_KEY_TEST}")
print(f"   Comprimento: {len(API_KEY_TEST)}")
print(f"   Começa com: {API_KEY_TEST[:20]}")
print(f"   Termina com: {API_KEY_TEST[-20:]}")

print(f"\n📝 Base String:")
base_string = f"{PARTNER_ID}{PATH}{TIMESTAMP}"
print(f"   {base_string}")
print(f"   Comprimento: {len(base_string)}")

print(f"\n📝 Assinaturas:")

for key_name, key in [("LIVE", API_KEY_LIVE), ("TEST", API_KEY_TEST)]:
    sig = hmac.new(
        key.encode('utf-8'),
        base_string.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    
    print(f"\n   {key_name}: {sig}")

# Tentar diferentes encodings
print(f"\n📝 Tentando DIFERENTES ENCODINGS da chave:")

for encoding in ['utf-8', 'ascii', 'latin-1']:
    try:
        sig = hmac.new(
            API_KEY_LIVE.encode(encoding),
            base_string.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        print(f"   {encoding}: {sig[:32]}...")
    except Exception as e:
        print(f"   {encoding}: ❌ Erro - {e}")

print("\n" + "="*70)
print("💡 AGORA VAMOS TESTAR COM ESSES VALORES")
print("="*70)

# Testar com valor fixo
import requests

SHOP_ID = "1616902621"
ACCESS_TOKEN = "624d57696477734248724d474444e4676"

for key_name, api_key in [("LIVE", API_KEY_LIVE), ("TEST", API_KEY_TEST)]:
    sig = hmac.new(
        api_key.encode('utf-8'),
        base_string.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    
    url = f"https://partner.shopeemobile.com/api/v2{PATH}"
    params = {
        "partner_id": PARTNER_ID,
        "shop_id": SHOP_ID,
        "access_token": ACCESS_TOKEN,
        "timestamp": TIMESTAMP,
        "sign": sig
    }
    
    print(f"\n🔬 Testando {key_name}:")
    
    try:
        r = requests.get(url, params=params, timeout=10)
        data = r.json()
        
        error = data.get("error", "")
        message = data.get("message", "")
        
        print(f"   Status: {r.status_code}")
        print(f"   Error: {error if error else '✅ OK'}")
        print(f"   Message: {message}")
        
    except Exception as e:
        print(f"   ❌ Erro: {e}")
