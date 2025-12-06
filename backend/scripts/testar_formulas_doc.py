#!/usr/bin/env python3
"""
Testar com base na documentação oficial
"""
import requests
import hmac
import hashlib
import time

PARTNER_ID = 2013808
PARTNER_KEY = "shpk4774635844546f67744c5150584a6e554b454f4a576c514b65734c664952"
ACCESS_TOKEN = "4f437355766f646b4f7370527a6e6f49"
SHOP_ID = 1616902621

def test_signature(path, timestamp, access_token, shop_id, formula_name, base_string_template):
    """Testa uma fórmula específica"""
    base_string = base_string_template.format(
        partner_id=PARTNER_ID,
        path=path,
        timestamp=timestamp,
        access_token=access_token,
        shop_id=shop_id
    )
    
    sign = hmac.new(
        PARTNER_KEY.encode(),
        base_string.encode(),
        hashlib.sha256
    ).hexdigest()
    
    url = f"https://partner.shopeemobile.com{path}"
    params = {
        "partner_id": PARTNER_ID,
        "timestamp": timestamp,
        "access_token": access_token,
        "shop_id": shop_id,
        "sign": sign,
        "page_size": 5,
        "offset": 0
    }
    
    print(f"\n{'='*70}")
    print(f"TESTE: {formula_name}")
    print(f"{'='*70}")
    print(f"Base string: {base_string}")
    print(f"Sign: {sign[:40]}...")
    
    response = requests.get(url, params=params, timeout=10)
    
    print(f"\nStatus: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        if "error" in data and data["error"]:
            print(f"❌ Erro: {data['error']}")
            print(f"   Msg: {data.get('message', 'N/A')}")
            return False
        else:
            print(f"✅ SUCESSO!")
            print(f"   Response: {data.get('response', {})}")
            return True
    else:
        print(f"❌ HTTP {response.status_code}")
        print(f"   Body: {response.text[:200]}")
        return False

print("="*70)
print("🔬 TESTANDO FÓRMULAS DE ASSINATURA")
print("="*70)

path = "/api/v2/product/get_item_list"
timestamp = int(time.time())

# TESTE 1: Fórmula padrão (documentação)
test_signature(
    path, timestamp, ACCESS_TOKEN, SHOP_ID,
    "FÓRMULA PADRÃO: partner_id + path + timestamp",
    "{partner_id}{path}{timestamp}"
)

# TESTE 2: Com access_token na base
test_signature(
    path, timestamp, ACCESS_TOKEN, SHOP_ID,
    "COM TOKEN: partner_id + path + timestamp + access_token",
    "{partner_id}{path}{timestamp}{access_token}"
)

# TESTE 3: Com shop_id
test_signature(
    path, timestamp, ACCESS_TOKEN, SHOP_ID,
    "COM SHOP: partner_id + path + timestamp + shop_id",
    "{partner_id}{path}{timestamp}{shop_id}"
)

# TESTE 4: Com ambos
test_signature(
    path, timestamp, ACCESS_TOKEN, SHOP_ID,
    "COMPLETO: partner_id + path + timestamp + access_token + shop_id",
    "{partner_id}{path}{timestamp}{access_token}{shop_id}"
)

print("\n" + "="*70)
print("FIM DOS TESTES")
print("="*70)
