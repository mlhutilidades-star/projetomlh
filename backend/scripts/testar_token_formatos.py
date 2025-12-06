#!/usr/bin/env python3
"""
Testar assinaturas com access_token em diferentes formatos
"""
import requests
import hmac
import hashlib
import time
import base64

PARTNER_ID = "2013808"
PARTNER_KEY = "shpk4774635844546f67744c5150584a6e554b454f4a576c514b65734c664952"
ACCESS_TOKEN = "624d57696477734248724d474444e4676"
SHOP_ID = "1616902621"

PATH = "/product/get_item_list"
TIMESTAMP = int(time.time())

print("="*70)
print("🔐 TESTAR COM ACCESS_TOKEN EM DIFERENTES FORMATOS")
print("="*70)

# Access token original
print(f"\nAccess Token Original: {ACCESS_TOKEN}")
print(f"Comprimento: {len(ACCESS_TOKEN)}")

# Tentar converter para diferentes formatos
try:
    # Hex para ASCII
    access_token_ascii = bytes.fromhex(ACCESS_TOKEN).decode('utf-8')
    print(f"Access Token (Hex→ASCII): {access_token_ascii}")
except:
    print(f"Access Token (Hex→ASCII): [não conseguiu converter]")
    access_token_ascii = None

# Base64
try:
    access_token_b64 = base64.b64encode(ACCESS_TOKEN.encode()).decode()
    print(f"Access Token (Base64): {access_token_b64}")
except:
    print(f"Access Token (Base64): [erro]")
    access_token_b64 = None

print("\n" + "="*70)
print("🔬 TESTANDO FÓRMULAS COM VARIAÇÕES")
print("="*70)

formulas_to_test = []

# Se conseguiu converter hex para ASCII
if access_token_ascii:
    formulas_to_test.extend([
        ("ASCII: partner+path+shop+ascii_token+time", f"{PARTNER_ID}{PATH}{SHOP_ID}{access_token_ascii}{TIMESTAMP}"),
        ("ASCII: path+shop+ascii_token+time", f"{PATH}{SHOP_ID}{access_token_ascii}{TIMESTAMP}"),
        ("ASCII: partner+path+ascii_token+time", f"{PARTNER_ID}{PATH}{access_token_ascii}{TIMESTAMP}"),
    ])

# Com base64
if access_token_b64:
    formulas_to_test.extend([
        ("Base64: partner+path+shop+b64_token+time", f"{PARTNER_ID}{PATH}{SHOP_ID}{access_token_b64}{TIMESTAMP}"),
    ])

# Tentar sem nenhuma conversão mas com ordem diferente
formulas_to_test.extend([
    ("Sem shop no hash: partner+path+time", f"{PARTNER_ID}{PATH}{TIMESTAMP}"),
    ("Com timestamp-1: partner+path+(time-1)", f"{PARTNER_ID}{PATH}{TIMESTAMP-1}"),
    ("Apenas path+time: path+time", f"{PATH}{TIMESTAMP}"),
])

def test_signature(name, base_string):
    """Testar uma assinatura"""
    signature = hmac.new(
        PARTNER_KEY.encode(),
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
            message = data.get("message", "")
            
            if error == "error_sign":
                status = "❌ WRONG SIGN"
            elif error == "":
                status = "✅ OK (erro vazio)"
            else:
                status = f"⚠️  OUTRO ERRO: {error}"
            
            return f"{status} | {message[:50]}"
        except:
            return f"Status {response.status_code}"
    except Exception as e:
        return f"ERRO: {str(e)[:40]}"

# Executar testes
for name, formula in formulas_to_test:
    result = test_signature(name, formula)
    print(f"\n{name}")
    print(f"  {result}")
    time.sleep(0.5)

print("\n" + "="*70)
