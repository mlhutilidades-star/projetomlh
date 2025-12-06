#!/usr/bin/env python3
"""
Testar diferentes fórmulas de assinatura para Shopee API
"""
import hmac
import hashlib
import time

# Suas credenciais
PARTNER_ID = "2013808"
PARTNER_KEY = "shpk4774635844546f67744c5150584a6e554b454f4a576c514b65734c664952"
ACCESS_TOKEN = "624d57696477734248724d474444e4676"
SHOP_ID = "1616902621"

PATH = "/product/get_item_list"
TIMESTAMP = int(time.time())

print("=" * 70)
print("🔐 TESTAR FÓRMULAS DE ASSINATURA SHOPEE")
print("=" * 70)
print(f"\nCredenciais:")
print(f"  Partner ID: {PARTNER_ID}")
print(f"  Shop ID: {SHOP_ID}")
print(f"  Access Token: {ACCESS_TOKEN[:20]}...")
print(f"  Path: {PATH}")
print(f"  Timestamp: {TIMESTAMP}")
print()

def test_formula(name, base_string):
    """Testar uma fórmula específica"""
    print(f"\n{'='*70}")
    print(f"📝 Fórmula {name}")
    print(f"{'='*70}")
    print(f"Base String: {base_string}")
    
    signature = hmac.new(
        PARTNER_KEY.encode(),
        base_string.encode(),
        hashlib.sha256
    ).hexdigest()
    
    print(f"Signature: {signature}")
    return signature

# Testar diferentes fórmulas
formulas = {
    "1 (ATUAL - SEM TOKEN)": f"{PARTNER_ID}{PATH}{TIMESTAMP}",
    
    "2 (COM TOKEN NO FINAL)": f"{PARTNER_ID}{PATH}{TIMESTAMP}{ACCESS_TOKEN}",
    
    "3 (ORDEM: PATH+SHOP+TOKEN+TIME)": f"{PATH}{SHOP_ID}{ACCESS_TOKEN}{TIMESTAMP}",
    
    "4 (ORDEM: PARTNER+SHOP+TOKEN+TIME)": f"{PARTNER_ID}{SHOP_ID}{ACCESS_TOKEN}{TIMESTAMP}",
    
    "5 (COM PIPE: partner_id|path|shop_id|access_token|timestamp)": f"{PARTNER_ID}|{PATH}|{SHOP_ID}|{ACCESS_TOKEN}|{TIMESTAMP}",
    
    "6 (COM AMPERSAND: path&shop_id&access_token&timestamp)": f"{PATH}&{SHOP_ID}&{ACCESS_TOKEN}&{TIMESTAMP}",
    
    "7 (APENAS: path+shop_id+access_token+timestamp)": f"{PATH}{SHOP_ID}{ACCESS_TOKEN}{TIMESTAMP}",
    
    "8 (ORDENADO: shop_id+path+access_token+timestamp)": f"{SHOP_ID}{PATH}{ACCESS_TOKEN}{TIMESTAMP}",
}

results = {}
for name, formula in formulas.items():
    sig = test_formula(name, formula)
    results[name] = sig

print(f"\n\n{'='*70}")
print("📊 RESUMO DE ASSINATURAS")
print(f"{'='*70}")
for name, sig in results.items():
    print(f"{name:50} → {sig[:32]}...")

print("\n" + "=" * 70)
print("💡 PRÓXIMOS PASSOS")
print("=" * 70)
print("""
1. Copie cada signature acima
2. Tente uma por vez no seu script
3. Execute sync_shopee_real.py novamente
4. Veja qual retorna sucesso (não "Wrong sign")

A fórmula correta será aquela que:
- NÃO retorna 403 error_sign
- Ou retorna um erro diferente (error_param, etc) indicando que a signature está OK
""")
