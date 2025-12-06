#!/usr/bin/env python3
"""
Diagnóstico completo - Verificar configurações Partner e OAuth
"""
import requests
import json
import time
import hmac
import hashlib

PARTNER_ID = "2013808"
PARTNER_KEY = "shpk4774635844546f67744c5150584a6e554b454f4a576c514b65734c664952"
REDIRECT_URI = "https://irc-devoted-analysts-cst.trycloudflare.com"
SHOPEE_API = "https://partner.shopeemobile.com/api/v2"

print("\n" + "="*80)
print("🔍 DIAGNÓSTICO PARTNER SHOPEE")
print("="*80)

print(f"\n✅ CONFIGURAÇÕES ATUAIS:")
print(f"   Partner ID: {PARTNER_ID}")
print(f"   Partner Key: {PARTNER_KEY[:20]}...{PARTNER_KEY[-10:]}")
print(f"   Redirect URI: {REDIRECT_URI}")

# TESTE 1: Verificar se Partner ID é válido
print("\n\n" + "="*80)
print("TEST 1: Listar informações básicas (sem autenticação)")
print("="*80)

try:
    response = requests.get(f"{SHOPEE_API}/public/ping")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text}")
except Exception as e:
    print(f"Erro: {e}")

# TESTE 2: Tentar autorização via URL com diferentes formatos
print("\n\n" + "="*80)
print("TEST 2: Testar URL de Autorização (vários formatos)")
print("="*80)

urls_para_testar = [
    # Formato 1: Simples
    f"{SHOPEE_API}/oauth/authorize?partner_id={PARTNER_ID}&redirect_uri={REDIRECT_URI}&response_type=code&state=test",
    
    # Formato 2: Com encoding
    f"{SHOPEE_API}/oauth/authorize?partner_id={PARTNER_ID}&redirect_uri=https%3A%2F%2Firc-devoted-analysts-cst.trycloudflare.com&response_type=code",
    
    # Formato 3: Possível endpoint alternativo
    f"https://partner.shopeemobile.com/api/oauth/authorize?partner_id={PARTNER_ID}&redirect_uri={REDIRECT_URI}&response_type=code",
]

for i, url in enumerate(urls_para_testar, 1):
    print(f"\n🔗 Formato {i}:")
    print(f"   {url[:80]}...")
    try:
        # Fazer HEAD request para testar sem seguir redirect
        response = requests.head(url, allow_redirects=False, timeout=5)
        print(f"   Status: {response.status_code}")
        if response.status_code in [301, 302, 303, 307, 308]:
            print(f"   Redirect: {response.headers.get('Location', 'N/A')[:100]}")
    except Exception as e:
        print(f"   Erro: {str(e)[:100]}")

# TESTE 3: Verificar assinatura HMAC
print("\n\n" + "="*80)
print("TEST 3: Verificar Assinatura HMAC")
print("="*80)

timestamp = int(time.time())
path = "/auth/token/get"

base_string = f"{PARTNER_ID}{path}{timestamp}"
print(f"\n📝 Base String: {base_string}")

sign = hmac.new(
    PARTNER_KEY.encode(),
    base_string.encode(),
    hashlib.sha256
).hexdigest()

print(f"🔐 Sign (SHA256): {sign}")

# Tentar também com partner_key sem o "shpk" prefix se houver
if PARTNER_KEY.startswith("shpk"):
    alt_key = PARTNER_KEY[4:]  # Remove "shpk"
    alt_sign = hmac.new(
        alt_key.encode(),
        base_string.encode(),
        hashlib.sha256
    ).hexdigest()
    print(f"🔐 Sign (sem prefix): {alt_sign}")

# TESTE 4: Investigar se é environment Test vs Live
print("\n\n" + "="*80)
print("TEST 4: Partner ID - Test vs Live")
print("="*80)

print(f"\n📊 Seu Partner ID: {PARTNER_ID}")
print(f"   Tipo: {'LIVE' if int(PARTNER_ID) > 1000000 else 'TEST'}")
print(f"   Status: Verificado manualmente em Shopee Seller Center")

# TESTE 5: Testar com exemplos conhecidos
print("\n\n" + "="*80)
print("TEST 5: Endpoints do Open Platform")
print("="*80)

endpoints_para_testar = [
    ("/shop/get_shop_info", "GET", {"access_token": "test"}),
    ("/product/get_item_list", "GET", {"access_token": "test"}),
]

for endpoint, method, params in endpoints_para_testar:
    print(f"\n🔗 {method} {endpoint}")
    try:
        if method == "GET":
            response = requests.get(f"{SHOPEE_API}{endpoint}", params=params, timeout=5)
        else:
            response = requests.post(f"{SHOPEE_API}{endpoint}", json=params, timeout=5)
        print(f"   Status: {response.status_code}")
        result = response.json()
        if "error" in result:
            print(f"   Error: {result.get('error')}")
            print(f"   Message: {result.get('message', 'N/A')}")
    except Exception as e:
        print(f"   Erro: {str(e)[:100]}")

# TESTE 6: Investigar error_not_found
print("\n\n" + "="*80)
print("TEST 6: Investigar error_not_found")
print("="*80)

print("\n📋 Possíveis causas de 'error_not_found' na autorização:")
print("   1. Partner ID não está registrado em Shopee")
print("   2. Redirect URI não corresponde à configuração em Shopee")
print("   3. URL base está errada (pode ser .com.br vs .sg)")
print("   4. Endpoint /oauth/authorize pode estar em outro lugar")
print("   5. Pode ser que Open Platform use fluxo diferente")

print("\n✅ AÇÕES PARA INVESTIGAR:")
print("   1. Verificar em Shopee: Settings > Partner Development")
print("   2. Confirmar se Partner ID está registrado como 'LIVE'")
print("   3. Confirmar Redirect URL Domain EXATA")
print("   4. Verificar se há diferença entre /api/v2 e /api")
print("   5. Pesquisar se Shopee Brasil tem endpoints diferentes")

print("\n" + "="*80)
