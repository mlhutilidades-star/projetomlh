#!/usr/bin/env python3
"""
Obter novo Access Token - Fluxo Interativo
"""
import requests
import hmac
import hashlib
import time
import webbrowser
from urllib.parse import urlparse, parse_qs

PARTNER_ID = "2013808"
PARTNER_KEY = "shpk4774635844546f67744c5150584a6e554b454f4a576c514b65734c664952"
SHOP_ID = "1616902621"
REDIRECT_URL = "https://lynette-semiexpositive-broadly.ngrok-free.dev/callback"

print("="*70)
print("🔐 OBTER NOVO ACCESS TOKEN - FLUXO COMPLETO")
print("="*70)

print("\n📝 PASSO 1: Autorizar no Shopee")
print("-"*70)

# Criar URL de autorização (endpoint correto para gerar o code)
# Doc: https://open.shopee.com/doc/v2#/partner/SHOP_API/get_shop_auth_partner
# Fórmula de assinatura para endpoints de auth: base_string = {partner_id}{path}{timestamp}
# Parâmetros obrigatórios: partner_id, timestamp, sign, redirect, state
AUTH_PATH = "/api/v2/shop/auth_partner"
auth_timestamp = int(time.time())
auth_signature = hmac.new(
    PARTNER_KEY.encode(),
    f"{PARTNER_ID}{AUTH_PATH}{auth_timestamp}".encode(),
    hashlib.sha256
).hexdigest()

auth_url = (
    "https://partner.shopeemobile.com" + AUTH_PATH +
    f"?partner_id={PARTNER_ID}"
    f"&timestamp={auth_timestamp}"
    f"&sign={auth_signature}"
    f"&redirect={REDIRECT_URL}"
    f"&state=state123"
)

print(f"\nAbra este link no navegador:")
print(f"{auth_url}")

print(f"\n⏳ Instruções:")
print(f"1. Clique no link acima")
print(f"2. Autorize a aplicação")
print(f"3. Você será redirecionado para: {REDIRECT_URL}?code=XXX&shop_id=YYY")
print(f"4. Copie o CODE da URL")

raw_input_code = input(f"\n💬 Cole a URL completa de callback ou apenas o CODE: ").strip()

if not raw_input_code:
    print("❌ Code vazio!")
    exit(1)

# Se o usuário colar a URL inteira, extrair o code
if raw_input_code.startswith("http://") or raw_input_code.startswith("https://"):
    parsed = urlparse(raw_input_code)
    qs = parse_qs(parsed.query)
    code = qs.get("code", [""])[0]
    shop_id_from_url = qs.get("shop_id", [""])[0]
else:
    code = raw_input_code
    shop_id_from_url = ""

if not code:
    print("❌ Não consegui extrair o code da URL.")
    exit(1)

print(f"\n✅ Code recebido: {code[:20]}...")
if shop_id_from_url:
    print(f"✅ Shop ID recebido: {shop_id_from_url}")

print("\n\n📝 PASSO 2: Trocar CODE por ACCESS TOKEN")
print("-"*70)

# URL para obter token
token_url = "https://partner.shopeemobile.com/api/v2/auth/token/get"
TIMESTAMP = int(time.time())
PATH = "/api/v2/auth/token/get"

# Assinar requisição
base_string = f"{PARTNER_ID}{PATH}{TIMESTAMP}"
signature = hmac.new(
    PARTNER_KEY.encode(),
    base_string.encode(),
    hashlib.sha256
).hexdigest()

target_shop_id = SHOP_ID
if shop_id_from_url:
    try:
        target_shop_id = int(shop_id_from_url)
    except ValueError:
        target_shop_id = SHOP_ID

body = {
    "code": code,
    "shop_id": target_shop_id
}

params = {
    "partner_id": PARTNER_ID,
    "timestamp": TIMESTAMP,
    "sign": signature
}

print(f"\n📤 Enviando requisição...")

try:
    r = requests.post(
        token_url,
        json=body,
        params=params,
        timeout=10
    )
    
    data = r.json()
    
    print(f"Status: {r.status_code}")
    
    if "error" in data and data["error"]:
        print(f"❌ Erro: {data['error']}")
        print(f"   Mensagem: {data.get('message', '')}")
    else:
        access_token = data.get("access_token", "")
        refresh_token = data.get("refresh_token", "")
        
        if access_token:
            print(f"\n✅ SUCESSO!")
            print(f"\n🎫 NOVOS TOKENS:")
            print(f"\nACCESS TOKEN:")
            print(f"{access_token}")
            print(f"\nREFRESH TOKEN:")
            print(f"{refresh_token}")
            
            print(f"\n\n📋 COPIE PARA .env:")
            print(f"="*70)
            print(f"SHOPEE_ACCESS_TOKEN=\"{access_token}\"")
            print(f"SHOPEE_REFRESH_TOKEN=\"{refresh_token}\"")
            print(f"="*70)
            
            # Salvar em arquivo
            with open("novo_tokens.txt", "w") as f:
                f.write(f"SHOPEE_ACCESS_TOKEN=\"{access_token}\"\n")
                f.write(f"SHOPEE_REFRESH_TOKEN=\"{refresh_token}\"\n")
            
            print(f"\n✅ Tokens também salvos em novo_tokens.txt")
        else:
            print(f"❌ Sem access_token na resposta")
            print(f"Response: {data}")
            
except Exception as e:
    print(f"❌ Erro: {e}")

print("\n" + "="*70)
