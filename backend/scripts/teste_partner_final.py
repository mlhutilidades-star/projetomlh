#!/usr/bin/env python3
"""
Última tentativa - Testar se Partner ID está realmente registrado
e tentar diferentes formatos de requisição
"""
import requests
import json
import time
import hmac
import hashlib

PARTNER_ID = "2013808"
PARTNER_KEY = "shpk4774635844546f67744c5150584a6e554b454f4a576c514b65734c664952"
SHOPEE_API = "https://partner.shopeemobile.com/api/v2"

print("\n" + "="*80)
print("🔍 VERIFICAÇÃO FINAL - Partner ID Registration")
print("="*80)

# TESTE 1: Tentar requisição com partner_id no header
print("\n TEST 1: COM PARTNER_ID NO HEADER")
print("-" * 80)

timestamp = int(time.time())
headers = {
    "partner_id": PARTNER_ID,
    "X-Partner-ID": PARTNER_ID,
    "Authorization": f"Bearer {PARTNER_ID}"
}

try:
    response = requests.get(
        f"{SHOPEE_API}/shop/get_shop_info",
        headers=headers,
        timeout=5
    )
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)[:200]}")
except Exception as e:
    print(f"Erro: {e}")

# TESTE 2: Requisição com assinatura no query string
print("\n\nTESTE 2: COM ASSINATURA NO QUERY STRING")
print("-" * 80)

path = "/shop/get_shop_info"
base_string = f"{PARTNER_ID}{path}{timestamp}"
sign = hmac.new(
    PARTNER_KEY.encode(),
    base_string.encode(),
    hashlib.sha256
).hexdigest()

params = {
    "partner_id": PARTNER_ID,
    "timestamp": timestamp,
    "sign": sign
}

try:
    response = requests.get(
        f"{SHOPEE_API}{path}",
        params=params,
        timeout=5
    )
    print(f"Status: {response.status_code}")
    result = response.json()
    print(f"Response: {json.dumps(result, indent=2)[:500]}")
except Exception as e:
    print(f"Erro: {e}")

# TESTE 3: Com access token dummy
print("\n\nTESTE 3: COM DUMMY ACCESS TOKEN")
print("-" * 80)

params_with_token = {
    "partner_id": PARTNER_ID,
    "access_token": "dummy_token_for_test",
    "timestamp": timestamp,
    "sign": sign
}

try:
    response = requests.get(
        f"{SHOPEE_API}{path}",
        params=params_with_token,
        timeout=5
    )
    print(f"Status: {response.status_code}")
    result = response.json()
    print(f"Response: {json.dumps(result, indent=2)[:500]}")
except Exception as e:
    print(f"Erro: {e}")

# TESTE 4: Listar Partner Info (se endpoint existir)
print("\n\nTESTE 4: ENDPOINTS ALTERNOS")
print("-" * 80)

endpoints_alt = [
    "/partner/get_info",
    "/partner/get_partner_info",
    "/auth/partner/info",
    "/open/partner",
]

for ep in endpoints_alt:
    try:
        response = requests.get(
            f"{SHOPEE_API}{ep}",
            params={"partner_id": PARTNER_ID},
            timeout=5
        )
        print(f"\n{ep}: Status {response.status_code}")
        if response.status_code in [200, 400, 403]:
            print(f"   {response.text[:200]}")
    except:
        pass

# TESTE 5: Verificar estrutura do Partner ID
print("\n\nTESTE 5: ANÁLISE DO PARTNER ID")
print("-" * 80)

print(f"Partner ID: {PARTNER_ID}")
print(f"Length: {len(PARTNER_ID)} dígitos")
print(f"Type: {'LIVE (7+ digits)' if len(PARTNER_ID) >= 7 else 'TEST'}")
print(f"\nPartner Key: {PARTNER_KEY[:10]}...{PARTNER_KEY[-10:]}")
print(f"Key Length: {len(PARTNER_KEY)} caracteres")
print(f"Key Prefix: {'shpk (valid)' if PARTNER_KEY.startswith('shpk') else 'INVALID PREFIX'}")

# CONCLUSÃO
print("\n\n" + "="*80)
print("💡 ANÁLISE E PRÓXIMOS PASSOS")
print("="*80)

print("""
Se todos os testes retornam "error_not_found" ou "There is no partner_id in query":

✅ OPÇÃO 1: Partner ID está desativado
   - Acesse https://seller.shopee.com.br/api/setting/partner-development
   - Verifique se Partner ID 2013808 está lá e ativado
   - Se não, crie um novo Partner no Shopee Developer Portal

✅ OPÇÃO 2: Usar um Partner ID TEST
   - Teste com: 1198503 (ou outro TEST ID que você tenha)
   - Veja se funciona
   - Se funcionar, use teste até ativar o LIVE

✅ OPÇÃO 3: Chamar suporte Shopee
   - Confirme que Partner 2013808 está registrado
   - Solicite ativação para Open Platform
   - Peça confirmação de Redirect URL Domain

✅ OPÇÃO 4: Usar Partner Key diferente
   - Pode haver vários "Live API Partner Key"
   - Tente copiar e colar novamente do Shopee
   - Certifique-se que não cortou ou adicionou espaços

IMPORTANTE: O erro "error_not_found" na AUTORIZAÇÃO é diferente de um erro na troca de token.
Isso sugere que o Partner ID não é reconhecido pelo servidor de autorização do Shopee.
""")

print("="*80)
