#!/usr/bin/env python3
"""
SHOPEE OPEN PLATFORM - FLUXO CORRETO DE OAUTH 2.0
Baseado na documentação oficial do Shopee Open Platform
"""
import requests
import json
import time
import hmac
import hashlib
from urllib.parse import urlencode, urlparse, parse_qs

PARTNER_ID = "2013808"
PARTNER_KEY = "shpk4774635844546f67744c5150584a6e554b454f4a576c514b65734c664952"
REDIRECT_URI = "https://irc-devoted-analysts-cst.trycloudflare.com/callback"
SHOPEE_API = "https://partner.shopeemobile.com/api/v2"

def generate_sign(path: str, timestamp: int, partner_key: str = PARTNER_KEY, partner_id: str = PARTNER_ID) -> str:
    """Gera assinatura HMAC-SHA256 para Shopee Open Platform"""
    base_string = f"{partner_id}{path}{timestamp}"
    sign = hmac.new(
        partner_key.encode(),
        base_string.encode(),
        hashlib.sha256
    ).hexdigest()
    return sign

def step1_generate_auth_url():
    """PASSO 1: Gerar URL de autorização"""
    auth_params = {
        "partner_id": PARTNER_ID,
        "redirect_uri": REDIRECT_URI,
        "response_type": "code",
        "state": "random_state_123"
    }
    
    auth_url = f"{SHOPEE_API}/oauth/authorize?" + urlencode(auth_params)
    return auth_url

def step2_exchange_code_for_token(code: str) -> dict:
    """PASSO 2: Trocar authorization code por access token"""
    timestamp = int(time.time())
    path = "/auth/token/get"
    sign = generate_sign(path, timestamp)
    
    # Parâmetros como QUERY STRING (não JSON!)
    params = {
        "partner_id": PARTNER_ID,
        "code": code,
        "grant_type": "authorization_code",
        "redirect_uri": REDIRECT_URI,
        "timestamp": timestamp,
        "sign": sign
    }
    
    print(f"\n🔗 Endpoint: {SHOPEE_API}{path}")
    print(f"📊 Parâmetros:")
    for k, v in params.items():
        if len(str(v)) > 50:
            print(f"   {k}: {str(v)[:30]}...{str(v)[-20:]}")
        else:
            print(f"   {k}: {v}")
    
    response = requests.get(
        f"{SHOPEE_API}{path}",
        params=params,
        timeout=10
    )
    
    print(f"\n📊 Status: {response.status_code}")
    data = response.json()
    
    if "error" in data and data["error"]:
        print(f"❌ Erro: {data['error']}")
        print(f"   Mensagem: {data.get('message', 'N/A')}")
        return None
    
    return data

def step3_get_shop_info(access_token: str) -> dict:
    """PASSO 3: Obter informações da loja (verificação)"""
    timestamp = int(time.time())
    path = "/shop/get_shop_info"
    sign = generate_sign(path, timestamp)
    
    params = {
        "access_token": access_token,
        "timestamp": timestamp,
        "sign": sign
    }
    
    response = requests.get(
        f"{SHOPEE_API}{path}",
        params=params,
        timeout=10
    )
    
    return response.json()

def main():
    print("\n" + "="*80)
    print("🚀 SHOPEE OPEN PLATFORM - OAUTH 2.0 FLOW CORRETO")
    print("="*80)
    
    print("""
DOCUMENTAÇÃO OFICIAL: https://open.shopee.com/
CONSOLE DE APPS: https://open.shopee.com/console/app
    """)
    
    # PASSO 1: Gerar URL de autorização
    print("\n✅ PASSO 1: GERAR URL DE AUTORIZAÇÃO")
    print("-" * 80)
    
    auth_url = step1_generate_auth_url()
    
    print(f"\n📋 URL DE AUTORIZAÇÃO (cole no navegador):\n")
    print(auth_url)
    print(f"\n💡 PRÓXIMAS AÇÕES:")
    print(f"   1. Cole a URL acima no seu navegador")
    print(f"   2. Faça login no Shopee (se não estiver logado)")
    print(f"   3. Clique em 'Autorizar' ou 'Permitir'")
    print(f"   4. Você será redirecionado para:")
    print(f"      {REDIRECT_URI}?code=CODE_AQUI&state=random_state_123")
    print(f"   5. Copie o CODE (não a URL inteira, apenas o código)")
    
    # PASSO 2: Receber authorization code
    print("\n\n✅ PASSO 2: RECEBER AUTHORIZATION CODE")
    print("-" * 80)
    
    code = input("\n📋 Cole o AUTHORIZATION CODE (code_xxxxxx): ").strip()
    
    if not code:
        print("❌ Código não fornecido!")
        return False
    
    # Limpar código se necessário
    if code.startswith("code="):
        code = code[5:]
    
    print(f"✅ Código recebido: {code[:50]}...")
    
    # PASSO 3: Trocar código por token
    print("\n\n✅ PASSO 3: TROCAR CÓDIGO POR ACCESS TOKEN")
    print("-" * 80)
    
    token_data = step2_exchange_code_for_token(code)
    
    if not token_data:
        return False
    
    access_token = token_data.get("access_token")
    refresh_token = token_data.get("refresh_token")
    shop_id = token_data.get("shop_id")
    expire_in = token_data.get("expire_in")
    
    if not access_token or not shop_id:
        print(f"\n❌ Resposta incompleta:")
        print(json.dumps(token_data, indent=2))
        return False
    
    print(f"\n✅ TOKENS OBTIDOS COM SUCESSO!")
    print(f"   Access Token: {access_token[:50]}...")
    print(f"   Shop ID: {shop_id}")
    if expire_in:
        print(f"   Expira em: {expire_in} segundos (~{expire_in//3600} horas)")
    
    # PASSO 4: Verificar acesso (opcional)
    print("\n\n✅ PASSO 4: VERIFICAR ACESSO À API")
    print("-" * 80)
    
    try:
        shop_info = step3_get_shop_info(access_token)
        
        if "error" in shop_info and shop_info["error"]:
            print(f"❌ Erro ao obter info: {shop_info['error']}")
        else:
            print(f"✅ Acesso à API confirmado!")
            if "response" in shop_info:
                print(f"   Shop Name: {shop_info['response'].get('shop_name', 'N/A')}")
                print(f"   Country: {shop_info['response'].get('country', 'N/A')}")
    except Exception as e:
        print(f"⚠️  Erro ao verificar: {e}")
    
    # RESULTADO FINAL
    print("\n\n" + "="*80)
    print("🎉 SUCESSO! TOKENS PRONTOS PARA USO")
    print("="*80)
    
    print(f"\n📝 COPIE EXATAMENTE PARA SEU .env:")
    print("-" * 80)
    print(f'SHOPEE_ACCESS_TOKEN="{access_token}"')
    print(f"SHOPEE_SHOP_ID={shop_id}")
    if refresh_token:
        print(f'SHOPEE_REFRESH_TOKEN="{refresh_token}"')
    print("-" * 80)
    
    print(f"\n💾 SALVE TAMBÉM EM LOCAL SEGURO:")
    print(f"   Refresh Token: {refresh_token}")
    print(f"   Expira em: {expire_in} segundos")
    print(f"   Data de Expiração: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time() + expire_in))}")
    
    print("\n\n✅ PRÓXIMOS PASSOS:")
    print("   1. Atualize o arquivo .env com os valores acima")
    print("   2. Execute: docker-compose up -d")
    print("   3. Execute: docker-compose exec backend python scripts/sync_tiny_real.py")
    print("   4. Execute: docker-compose exec backend python scripts/sync_shopee_real.py")
    print("   5. Acesse http://localhost:3000/dashboard para ver os dados!")
    
    print("\n" + "="*80 + "\n")
    
    return True

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
