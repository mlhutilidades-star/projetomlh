#!/usr/bin/env python3
"""
Obter Shopee Access Token - VERSÃO MANUAL SEM BROWSER
Para quando a autorização via URL retorna erro
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

def generate_sign(path: str, timestamp: int, partner_key: str = PARTNER_KEY) -> str:
    """Gerar assinatura HMAC SHA256"""
    base_string = f"{PARTNER_ID}{path}{timestamp}"
    sign = hmac.new(
        partner_key.encode(),
        base_string.encode(),
        hashlib.sha256
    ).hexdigest()
    return sign

print("\n" + "="*80)
print("📱 SHOPEE OPEN PLATFORM - ALTERNATIVA MANUAL")
print("="*80)

# INVESTIGAÇÃO: Verificar se temos um CODE válido guardado
print("\n💡 OPÇÃO 1: Se você já tem um CODE do Shopee")
print("-" * 80)
print("\nSe você já autorizou em Shopee e tem um CODE:")
print("1. Vá para: https://partner.shopeemobile.com/api/v2/oauth/authorize?partner_id=2013808&redirect_uri=https://irc-devoted-analysts-cst.trycloudflare.com&response_type=code&state=test123")
print("2. Se funcionar: clique em Autorizar")
print("3. Se redirecionar com ?code=ABC: copie o CODE")
print("4. Cole aqui")

has_code = input("\nVocê tem um CODE de autorização? (s/n): ").strip().lower()

if has_code == 's':
    code = input("Cole o CODE (code_xxxxx...): ").strip()
    if code.startswith("code="):
        code = code[5:]
elif has_code == 'n':
    print("\n❌ Sem um CODE válido, não é possível continuar.")
    print("\n💡 POSSÍVEIS PROBLEMAS:")
    print("   1. Partner ID não está registrado na Open Platform")
    print("   2. Redirect URL não foi configurada em Shopee")
    print("   3. Partner ID está em ambiente TEST, não LIVE")
    print("   4. Conta do Shopee não tem acesso à Open Platform")
    print("\n✅ SOLUÇÃO:")
    print("   1. Acesse: https://seller.shopee.com.br/api/setting/partner-development")
    print("   2. Verifique se Partner ID está lá")
    print("   3. Se não estiver, crie um novo Partner no Shopee Developer Portal")
    print("   4. Configure o Redirect URL Domain EXATAMENTE como: https://irc-devoted-analysts-cst.trycloudflare.com")
    print("   5. Depois volte aqui")
    exit(1)

print(f"\n✅ CODE recebido: {code[:50]}...")

# PASSO 1: Trocar code por token
print("\n\n" + "="*80)
print("🔄 PASSO 1: TROCAR CODE POR ACCESS TOKEN")
print("="*80)

timestamp = int(time.time())
path = "/auth/token/get"
sign = generate_sign(path, timestamp)

token_params = {
    "partner_id": PARTNER_ID,
    "code": code,
    "grant_type": "authorization_code",
    "redirect_uri": REDIRECT_URI,
    "timestamp": timestamp,
    "sign": sign
}

print(f"\n🔗 Endpoint: {SHOPEE_API}{path}")
print(f"\n📊 Parâmetros:")
for k, v in token_params.items():
    if len(str(v)) > 60:
        print(f"   {k}: {str(v)[:60]}...")
    else:
        print(f"   {k}: {v}")

print(f"\n⏳ Enviando requisição...")

try:
    response = requests.get(
        f"{SHOPEE_API}{path}",
        params=token_params,
        timeout=10
    )
    
    print(f"\n📊 Status: {response.status_code}")
    result = response.json()
    
    if "error" not in result or result.get("error") is None:
        print(f"✅ RESPOSTA:\n{json.dumps(result, indent=2, ensure_ascii=False)}")
        
        access_token = result.get("access_token")
        shop_id = result.get("shop_id")
        refresh_token = result.get("refresh_token", "")
        
        if access_token and shop_id:
            print("\n\n" + "="*80)
            print("🎉 SUCESSO!")
            print("="*80)
            print(f"\n✅ Access Token: {access_token}")
            print(f"✅ Shop ID: {shop_id}")
            if refresh_token:
                print(f"✅ Refresh Token: {refresh_token}")
            
            print("\n\n📝 COPIE PARA .env:")
            print("-" * 80)
            print(f'SHOPEE_ACCESS_TOKEN="{access_token}"')
            print(f"SHOPEE_SHOP_ID={shop_id}")
            if refresh_token:
                print(f'SHOPEE_REFRESH_TOKEN="{refresh_token}"')
            print("-" * 80)
        else:
            print("\n❌ Resposta não contém access_token ou shop_id")
    else:
        error = result.get("error", "Desconhecido")
        message = result.get("message", "N/A")
        print(f"\n❌ ERRO: {error}")
        print(f"   Mensagem: {message}")
        
        print("\n💡 DIAGNÓSTICO:")
        if error == "error_not_found":
            print("   - CODE expirou (válido por ~10 min)")
            print("   - CODE é inválido")
            print("   - Obtenha um novo CODE")
        elif error == "error_sign":
            print("   - Assinatura HMAC incorreta")
            print("   - Verifique Partner Key")
        elif error == "invalid_grant":
            print("   - CODE não corresponde ao que foi autorizado")
            print("   - Redirect URI não corresponde")
        
except Exception as e:
    print(f"\n❌ ERRO DE CONEXÃO: {e}")

print("\n" + "="*80)
