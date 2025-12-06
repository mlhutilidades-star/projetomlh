#!/usr/bin/env python3
"""
Testar TODAS as fórmulas possíveis de HMAC para Shopee API
Baseado em tentativa e erro com os parâmetros que temos
"""
import hmac
import hashlib
import time

PARTNER_ID = "2013808"
PARTNER_KEY = "shpk4774635844546f67744c5150584a6e554b454f4a576c514b65734c664952"
ACCESS_TOKEN = "54666a41686a75534a61527167454353"
SHOP_ID = "1616902621"
PATH = "/product/get_item_list"
TIMESTAMP = 1764969800

def test_formula(name, base_string):
    """Testar uma fórmula de assinatura"""
    sig = hmac.new(
        PARTNER_KEY.encode(),
        base_string.encode(),
        hashlib.sha256
    ).hexdigest()
    print(f"\n{name}")
    print(f"  Base: {base_string[:80]}...")
    print(f"  Sign: {sig}")
    return sig

print("\n" + "="*80)
print("🔍 TESTANDO TODAS AS FÓRMULAS DE ASSINATURA SHOPEE")
print("="*80)

print("\n\n### FÓRMULAS SEM ACCESS_TOKEN (Partner-only):")
test_formula("1. Partner + Path + Time", f"{PARTNER_ID}{PATH}{TIMESTAMP}")
test_formula("2. Partner + Path + ShopID + Time", f"{PARTNER_ID}{PATH}{SHOP_ID}{TIMESTAMP}")

print("\n\n### FÓRMULAS COM ACCESS_TOKEN (Authenticated):")
test_formula("3. Partner + Path + Time (ignore token)", f"{PARTNER_ID}{PATH}{TIMESTAMP}")
test_formula("4. Path + ShopID + Time + Token", f"{PATH}{SHOP_ID}{TIMESTAMP}{ACCESS_TOKEN}")
test_formula("5. Path + ShopID + AccessToken + Time", f"{PATH}{SHOP_ID}{ACCESS_TOKEN}{TIMESTAMP}")
test_formula("6. Partner + Path + ShopID + Time + Token", f"{PARTNER_ID}{PATH}{SHOP_ID}{TIMESTAMP}{ACCESS_TOKEN}")
test_formula("7. Partner + Path + Token + Time", f"{PARTNER_ID}{PATH}{ACCESS_TOKEN}{TIMESTAMP}")
test_formula("8. ShopID + Path + Token + Time", f"{SHOP_ID}{PATH}{ACCESS_TOKEN}{TIMESTAMP}")
test_formula("9. Token + Path + ShopID + Time", f"{ACCESS_TOKEN}{PATH}{SHOP_ID}{TIMESTAMP}")
test_formula("10. Time + Partner + Path + Token", f"{TIMESTAMP}{PARTNER_ID}{PATH}{ACCESS_TOKEN}")

print("\n\n" + "="*80)
print("NOTA: Copie os valores acima e compare com o erro 'error_sign' do Shopee")
print("Se NENHUM funcionar, o problema pode ser:")
print("  - Access token expirou")
print("  - Partner Key está incorreta")
print("  - Shopee API requer um header especial ou encoding diferente")
print("="*80 + "\n")
