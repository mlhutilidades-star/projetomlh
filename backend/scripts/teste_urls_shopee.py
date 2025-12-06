#!/usr/bin/env python3
"""
Testar diferentes URLs base do Shopee para Brasil
"""
import requests
import json

PARTNER_ID = "2013808"

urls_base_para_testar = [
    # URLs conhecidas
    "https://partner.shopeemobile.com/api/v2",           # Global
    "https://partner.shopeemobile.com/api",              # Global v1
    "https://partner.shopee.com.br/api/v2",              # Brasil v2
    "https://partner.shopee.com.br/api",                 # Brasil v1
    "https://partner.shopee.sg/api/v2",                  # Singapore
    "https://partner-br.shopeemobile.com/api/v2",        # BR específico
    "https://partner.shopeemobile.com.br/api/v2",        # BR no domínio
    "https://open-api.shopee.com.br/v2",                 # Open API
    "https://open-api.shopee.com/v2",                    # Open API global
    "https://shopee.dev.sg/api/v2",                      # Dev
]

print("\n" + "="*80)
print("🔍 TESTANDO DIFERENTES URLs BASE DO SHOPEE")
print("="*80)

for url_base in urls_base_para_testar:
    print(f"\n🔗 Testando: {url_base}")
    
    try:
        # Tentar /public/ping
        response = requests.get(f"{url_base}/public/ping", timeout=3)
        print(f"   /public/ping: {response.status_code}", end="")
        if response.status_code == 200:
            print(" ✅ FUNCIONA!")
            print(f"      Response: {response.text}")
        else:
            print(f" ❌ (error: {response.json().get('error', 'unknown')})")
    except Exception as e:
        print(f"   /public/ping: ❌ {str(e)[:50]}")
    
    try:
        # Tentar /shop/get_shop_info com partner_id
        params = {"partner_id": PARTNER_ID, "access_token": "test"}
        response = requests.get(f"{url_base}/shop/get_shop_info", params=params, timeout=3)
        print(f"   /shop/get_shop_info: {response.status_code}", end="")
        result = response.json()
        if "error" in result:
            print(f" - error: {result['error']}")
        else:
            print(f" ✅")
    except Exception as e:
        print(f"   /shop/get_shop_info: ❌ {str(e)[:50]}")

print("\n\n" + "="*80)
print("💡 INVESTIGAÇÃO: PARTNER ID EM TEST vs LIVE")
print("="*80)

# Verificar se Partner ID 2013808 é LIVE ou TEST
# Normalmente:
# - TEST: IDs 6 dígitos ou menores
# - LIVE: IDs 7+ dígitos

partner_id_num = int(PARTNER_ID)
print(f"\nPartner ID: {PARTNER_ID}")
print(f"Número de dígitos: {len(PARTNER_ID)}")
print(f"Tipo identificado: {'LIVE (7+ dígitos)' if len(PARTNER_ID) >= 7 else 'TEST (6 dígitos ou menos)'}")

# Possível Partner ID TEST para referência
test_id_example = "1198503"
print(f"\nExemplo de TEST Partner ID: {test_id_example}")

print("\n\n" + "="*80)
print("⚠️  PRÓXIMOS PASSOS")
print("="*80)
print("\n1. Verifique qual URL funciona (a que retorna status 200)")
print("2. Se nenhuma funcionar, o Partner ID pode não estar ativado")
print("3. Verifique em Shopee Partner Portal se está ativado para Open Platform")
print("4. Possível: Partner ID está em ambiente TEST, não LIVE")
