#!/usr/bin/env python3
"""
Obter novo Access Token do Shopee usando o código de autorização
"""
import requests
import hmac
import hashlib
import time
import json

# Dados da sua app
PARTNER_ID = 2013808
PARTNER_KEY = "shpk4774635844546f67744c5150584a6e554b454f4a576c514b65734c664952"

# Código recebido após autorização
AUTH_CODE = "766f6d68624375495877725955436665"
SHOP_ID = 1616902621

# URL do Shopee
TOKEN_URL = "https://partner.shopeemobile.com/api/v2/auth/token/get"

def sign_request(partner_id, path, timestamp, partner_key):
    """Gerar assinatura HMAC"""
    message = f"{partner_id}{path}{timestamp}"
    signature = hmac.new(
        partner_key.encode(),
        message.encode(),
        hashlib.sha256
    ).hexdigest()
    return signature

# Preparar dados
timestamp = int(time.time())
path = "/api/v2/auth/token/get"
signature = sign_request(PARTNER_ID, path, timestamp, PARTNER_KEY)

# Body da requisição
body = {
    "code": AUTH_CODE,
    "shop_id": SHOP_ID
}

# Headers
headers = {
    "Content-Type": "application/json",
    "X-Shopee-Access-Token": ""
}

# Parâmetros da URL
params = {
    "partner_id": PARTNER_ID,
    "timestamp": timestamp,
    "sign": signature
}

print("=" * 60)
print("🔐 OBTER NOVO TOKEN SHOPEE")
print("=" * 60)
print(f"\n📊 Parâmetros:")
print(f"  Partner ID: {PARTNER_ID}")
print(f"  Shop ID: {SHOP_ID}")
print(f"  Auth Code: {AUTH_CODE}")
print(f"  Timestamp: {timestamp}")
print(f"  Signature: {signature}")

print(f"\n📤 Enviando requisição para: {TOKEN_URL}")

try:
    response = requests.post(
        TOKEN_URL,
        json=body,
        headers=headers,
        params=params,
        timeout=10
    )
    
    print(f"\n📥 Resposta (Status: {response.status_code}):")
    print(response.text)
    
    if response.status_code == 200:
        data = response.json()
        
        if "data" in data:
            print("\n" + "=" * 60)
            print("✅ SUCESSO!")
            print("=" * 60)
            
            access_token = data["data"].get("access_token", "")
            refresh_token = data["data"].get("refresh_token", "")
            
            print(f"\n🎫 ACCESS TOKEN:")
            print(f"   {access_token}")
            print(f"\n🔄 REFRESH TOKEN:")
            print(f"   {refresh_token}")
            
            print("\n" + "=" * 60)
            print("📝 COPIE PARA .env:")
            print("=" * 60)
            print(f"SHOPEE_ACCESS_TOKEN={access_token}")
            print(f"SHOPEE_REFRESH_TOKEN={refresh_token}")
            
        else:
            print(f"\n❌ Erro: {data.get('error', 'Desconhecido')}")
            print(f"   Mensagem: {data.get('message', 'Sem detalhes')}")
    else:
        print(f"\n❌ Erro HTTP: {response.status_code}")
        
except Exception as e:
    print(f"\n❌ Erro na requisição: {e}")

print("\n" + "=" * 60)
