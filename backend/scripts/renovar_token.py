#!/usr/bin/env python3
"""
Renovar Access Token usando Refresh Token
Documentação: https://open.shopee.com/documents/v2/v2.auth_token.refresh_token.post
"""
import requests
import json
import time
import hmac
import hashlib

PARTNER_ID = "2013808"
PARTNER_KEY = "shpk4774635844546f67744c5150584a6e554b454f4a576c514b65734c664952"
REFRESH_TOKEN = "654452797475516454585a6e6f777670"
SHOPEE_API = "https://partner.shopeemobile.com/api/v2"

def generate_sign(path: str, timestamp: int) -> str:
    """Gerar assinatura HMAC"""
    base_string = f"{PARTNER_ID}{path}{timestamp}"
    return hmac.new(
        PARTNER_KEY.encode(),
        base_string.encode(),
        hashlib.sha256
    ).hexdigest()

print("\n" + "="*80)
print("🔄 RENOVANDO ACCESS TOKEN")
print("="*80)

timestamp = int(time.time())
path = "/auth/access_token/get"
sign = generate_sign(path, timestamp)

params = {
    "partner_id": PARTNER_ID,
    "timestamp": timestamp,
    "sign": sign,
}

body = {
    "refresh_token": REFRESH_TOKEN,
    "shop_id": 1616902621,
    "partner_id": int(PARTNER_ID)
}

print(f"\n🔗 Endpoint: {SHOPEE_API}{path}")
print(f"📊 Query Params: {params}")
print(f"📦 Body: {body}")

try:
    response = requests.post(
        f"{SHOPEE_API}{path}",
        params=params,
        json=body,
        timeout=10
    )
    
    print(f"\n📊 Status: {response.status_code}")
    result = response.json()
    print(f"📄 Resposta:\n{json.dumps(result, indent=2, ensure_ascii=False)}")
    
    if "access_token" in result:
        access_token = result["access_token"]
        refresh_token = result.get("refresh_token", "")
        expire_in = result.get("expire_in", "")
        
        print("\n\n" + "="*80)
        print("🎉 TOKEN RENOVADO COM SUCESSO!")
        print("="*80)
        
        print(f"\n✅ Novo Access Token: {access_token}")
        if refresh_token:
            print(f"✅ Novo Refresh Token: {refresh_token}")
        if expire_in:
            print(f"✅ Expira em: {expire_in} segundos (~{expire_in//3600} horas)")
        
        print("\n\n📝 COPIE PARA .env:")
        print("-" * 80)
        print(f'SHOPEE_ACCESS_TOKEN="{access_token}"')
        if refresh_token:
            print(f'SHOPEE_REFRESH_TOKEN="{refresh_token}"')
        print("-" * 80)
        
    else:
        error = result.get("error", "Desconhecido")
        message = result.get("message", "N/A")
        print(f"\n❌ ERRO: {error}")
        print(f"   Mensagem: {message}")

except Exception as e:
    print(f"\n❌ ERRO DE CONEXÃO: {e}")

print("\n" + "="*80)
