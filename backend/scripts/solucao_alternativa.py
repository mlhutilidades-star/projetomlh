#!/usr/bin/env python3
"""
SOLUÇÃO FINAL: Simular fluxo OAuth sem browser
Se você tiver um shop_id, podemos usar autorização implícita
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

def generate_sign(path: str, timestamp: int, partner_key: str = PARTNER_KEY, extra_path: str = "") -> str:
    """Gerar assinatura HMAC SHA256"""
    if extra_path:
        base_string = f"{PARTNER_ID}{path}/{extra_path}{timestamp}"
    else:
        base_string = f"{PARTNER_ID}{path}{timestamp}"
    sign = hmac.new(
        partner_key.encode(),
        base_string.encode(),
        hashlib.sha256
    ).hexdigest()
    return sign

print("\n" + "="*80)
print("🚀 SHOPEE - OBTER TOKENS (SOLUÇÃO ALTERNATIVA)")
print("="*80)

print("\n📋 OPÇÃO A: Se você tem um SHOP_ID")
print("-" * 80)
print("Se você já tem um shop_id (pode estar em outro projeto):")

shop_id_input = input("\nCole o SHOP_ID (ou deixe vazio): ").strip()

if shop_id_input:
    shop_id = shop_id_input
    print(f"\n✅ Usando Shop ID: {shop_id}")
    
    # Gerar tokens usando shop_id
    timestamp = int(time.time())
    path = "/auth/access_token"
    sign = generate_sign(path, timestamp, extra_path=shop_id)
    
    params = {
        "partner_id": PARTNER_ID,
        "shop_id": shop_id,
        "timestamp": timestamp,
        "sign": sign
    }
    
    print(f"\n🔗 Tentando obter access token com shop_id...")
    print(f"📊 Parâmetros: {json.dumps(params, indent=2)}")
    
    try:
        response = requests.get(
            f"{SHOPEE_API}{path}",
            params=params,
            timeout=5
        )
        print(f"\nStatus: {response.status_code}")
        result = response.json()
        print(f"Response: {json.dumps(result, indent=2)}")
        
        if "access_token" in result:
            print("\n✅ ACCESS TOKEN OBTIDO!")
            print(f'SHOPEE_ACCESS_TOKEN="{result["access_token"]}"')
            print(f"SHOPEE_SHOP_ID={shop_id}")
    except Exception as e:
        print(f"Erro: {e}")

print("\n\n📋 OPÇÃO B: Obter CODE da URL manualmente")
print("-" * 80)

auth_url = f"{SHOPEE_API}/oauth/authorize?partner_id={PARTNER_ID}&redirect_uri={REDIRECT_URI}&response_type=code&state=test123"
print(f"\n1. Cole esta URL no navegador:")
print(f"\n{auth_url}\n")

code_input = input("2. Após autorizar, cole o CODE aqui (code_xxxxx): ").strip()

if code_input:
    code = code_input
    if code.startswith("code="):
        code = code[5:]
    
    print(f"\n✅ CODE recebido: {code[:40]}...")
    
    # Trocar code por token
    timestamp = int(time.time())
    path = "/auth/token/get"
    sign = generate_sign(path, timestamp)
    
    params = {
        "partner_id": PARTNER_ID,
        "code": code,
        "grant_type": "authorization_code",
        "redirect_uri": REDIRECT_URI,
        "timestamp": timestamp,
        "sign": sign
    }
    
    print(f"\n🔄 Trocando código por token...")
    
    try:
        response = requests.get(
            f"{SHOPEE_API}{path}",
            params=params,
            timeout=5
        )
        
        print(f"Status: {response.status_code}")
        result = response.json()
        
        if "error" in result:
            print(f"\n❌ ERRO: {result['error']}")
            print(f"   {result.get('message', '')}")
            
            if result['error'] == "error_not_found":
                print("\n💡 DICA: Código expirou ou inválido")
                print("   Códigos são válidos por ~10 minutos")
                print("   Tente novamente com um novo código")
        else:
            access_token = result.get("access_token")
            shop_id = result.get("shop_id")
            
            if access_token and shop_id:
                print(f"\n✅ SUCESSO!")
                print(f"\n📝 COPIE PARA .env:")
                print(f'SHOPEE_ACCESS_TOKEN="{access_token}"')
                print(f"SHOPEE_SHOP_ID={shop_id}")
            else:
                print(f"\nResposta: {json.dumps(result, indent=2)}")
    
    except Exception as e:
        print(f"Erro: {e}")

print("\n\n" + "="*80)
