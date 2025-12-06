#!/usr/bin/env python3
"""
Testar cada fórmula de assinatura contra a API Shopee
"""
import requests
import hmac
import hashlib
import time
import json

PARTNER_ID = "2013808"
PARTNER_KEY = "shpk4774635844546f67744c5150584a6e554b454f4a576c514b65734c664952"
ACCESS_TOKEN = "624d57696477734248724d474444e4676"
SHOP_ID = "1616902621"

PATH = "/product/get_item_list"
TIMESTAMP = int(time.time())

def test_api_with_signature(formula_name, base_string):
    """Testar uma assinatura contra a API Shopee"""
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
    
    print(f"\n{'='*70}")
    print(f"🔬 Testando: {formula_name}")
    print(f"{'='*70}")
    print(f"Base String: {base_string[:80]}...")
    print(f"Signature: {signature[:40]}...")
    
    try:
        response = requests.get(
            url,
            params=params,
            timeout=10
        )
        
        print(f"Status: {response.status_code}")
        
        try:
            data = response.json()
            
            if "error" in data:
                error = data.get("error", "")
                message = data.get("message", "")
                
                if error == "error_sign":
                    print(f"❌ ERRADO - {error}: {message}")
                elif error == "":
                    print(f"✅ POSSÍVEL SUCESSO - Erro vazio")
                    print(f"   Resposta: {str(data)[:200]}")
                else:
                    print(f"⚠️  POSSÍVEL CORRETO - Erro diferente: {error}")
                    print(f"   Mensagem: {message}")
                    print(f"   (Signature pode estar correta, mas faltam parâmetros)")
            else:
                print(f"✅ POSSÍVEL SUCESSO!")
                print(f"   Resposta: {str(data)[:200]}")
                
        except:
            print(f"Resposta (raw): {response.text[:200]}")
            
    except Exception as e:
        print(f"❌ Erro: {e}")

# Formulas a testar
formulas = {
    "1 - ATUAL (SEM TOKEN)": f"{PARTNER_ID}{PATH}{TIMESTAMP}",
    "2 - COM TOKEN NO FINAL": f"{PARTNER_ID}{PATH}{TIMESTAMP}{ACCESS_TOKEN}",
    "3 - PATH+SHOP+TOKEN+TIME": f"{PATH}{SHOP_ID}{ACCESS_TOKEN}{TIMESTAMP}",
    "4 - PARTNER+SHOP+TOKEN+TIME": f"{PARTNER_ID}{SHOP_ID}{ACCESS_TOKEN}{TIMESTAMP}",
    "5 - COM PIPE": f"{PARTNER_ID}|{PATH}|{SHOP_ID}|{ACCESS_TOKEN}|{TIMESTAMP}",
    "6 - COM AMPERSAND": f"{PATH}&{SHOP_ID}&{ACCESS_TOKEN}&{TIMESTAMP}",
    "7 - SEM PARTNER": f"{PATH}{SHOP_ID}{ACCESS_TOKEN}{TIMESTAMP}",
    "8 - SHOP+PATH+TOKEN+TIME": f"{SHOP_ID}{PATH}{ACCESS_TOKEN}{TIMESTAMP}",
}

print("="*70)
print("🔐 TESTANDO ASSINATURAS CONTRA API SHOPEE")
print("="*70)

for name, formula in formulas.items():
    test_api_with_signature(name, formula)
    time.sleep(1)  # Aguardar entre requisições

print(f"\n\n{'='*70}")
print("✅ TESTE CONCLUÍDO")
print("="*70)
print("Procure por resposta diferente de 'error_sign' para encontrar a fórmula correta!")
