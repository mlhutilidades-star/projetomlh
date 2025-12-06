#!/usr/bin/env python3
"""
SOLUÇÃO DIRETA - Clicar em "Authorize" no Shopee Developer Portal
Baseado nas imagens enviadas
"""
import requests
import json
import time
import hmac
import hashlib

PARTNER_ID = "2013808"
PARTNER_KEY = "shpk4774635844546f67744c5150584a6e554b454f4a576c514b65734c664952"
REDIRECT_URI = "https://irc-devoted-analysts-cst.trycloudflare.com/callback"
SHOPEE_API = "https://partner.shopeemobile.com/api/v2"

def generate_sign(path: str, timestamp: int) -> str:
    """Gerar assinatura HMAC SHA256"""
    base_string = f"{PARTNER_ID}{path}{timestamp}"
    sign = hmac.new(
        PARTNER_KEY.encode(),
        base_string.encode(),
        hashlib.sha256
    ).hexdigest()
    return sign

print("\n" + "="*80)
print("🚀 SHOPEE - MÉTODO DIRETO VIA DEVELOPER PORTAL")
print("="*80)

print("""
📋 PASSO A PASSO:

1. Acesse: https://seller.shopee.com.br/api/setting/partner-development

2. Na seção "GestaoMLH" (sua app), clique em "Authorize" ao lado de:
   - Live Partner_id: 2013808

3. Vai abrir um popup pedindo Redirect URL

4. Cole EXATAMENTE: https://irc-devoted-analysts-cst.trycloudflare.com/callback

5. Clique em "Next"

6. Você será redirecionado para uma URL tipo:
   https://irc-devoted-analysts-cst.trycloudflare.com/callback?code=XXXXX&shop_id=YYYY

7. COPIE TODA A URL e cole aqui
""")

print("="*80)

redirected_url = input("\n📋 Cole a URL COMPLETA após autorizar: ").strip()

if not redirected_url:
    print("❌ URL não fornecida")
    exit(1)

# Extrair code e shop_id da URL
print(f"\n🔍 Analisando URL...")

try:
    from urllib.parse import urlparse, parse_qs
    
    parsed = urlparse(redirected_url)
    params = parse_qs(parsed.query)
    
    code = params.get('code', [None])[0]
    shop_id = params.get('shop_id', [None])[0]
    main_account_id = params.get('main_account_id', [None])[0]
    
    print(f"\n✅ Parâmetros extraídos:")
    print(f"   CODE: {code[:50] if code else 'NÃO ENCONTRADO'}...")
    print(f"   SHOP_ID: {shop_id if shop_id else 'NÃO ENCONTRADO'}")
    if main_account_id:
        print(f"   MAIN_ACCOUNT_ID: {main_account_id}")
    
    if not code:
        print("\n❌ CODE não encontrado na URL!")
        print("   Verifique se copiou a URL completa")
        exit(1)
    
    # PASSO 2: Trocar code por access token
    print("\n\n" + "="*80)
    print("🔄 TROCANDO CODE POR ACCESS TOKEN")
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
    
    if shop_id:
        token_params["shop_id"] = shop_id
    
    print(f"\n🔗 Endpoint: {SHOPEE_API}{path}")
    print(f"\n📊 Parâmetros:")
    for k, v in token_params.items():
        if k in ['code', 'sign'] and len(str(v)) > 60:
            print(f"   {k}: {str(v)[:30]}...{str(v)[-20:]}")
        else:
            print(f"   {k}: {v}")
    
    print(f"\n⏳ Enviando requisição...")
    
    response = requests.get(
        f"{SHOPEE_API}{path}",
        params=token_params,
        timeout=10
    )
    
    print(f"\n📊 Status: {response.status_code}")
    result = response.json()
    
    print(f"📄 Resposta completa:")
    print(json.dumps(result, indent=2, ensure_ascii=False))
    
    if "access_token" in result:
        access_token = result["access_token"]
        refresh_token = result.get("refresh_token", "")
        expire_in = result.get("expire_in", "")
        final_shop_id = result.get("shop_id", shop_id)
        
        print("\n\n" + "="*80)
        print("🎉 SUCESSO! TOKENS OBTIDOS!")
        print("="*80)
        
        print(f"\n✅ Access Token: {access_token}")
        print(f"✅ Shop ID: {final_shop_id}")
        if refresh_token:
            print(f"✅ Refresh Token: {refresh_token}")
        if expire_in:
            print(f"✅ Expira em: {expire_in} segundos (~{expire_in//3600} horas)")
        
        print("\n\n📝 COPIE PARA .env:")
        print("-" * 80)
        print(f'SHOPEE_ACCESS_TOKEN="{access_token}"')
        print(f'SHOPEE_SHOP_ID={final_shop_id}')
        if refresh_token:
            print(f'SHOPEE_REFRESH_TOKEN="{refresh_token}"')
        print("-" * 80)
        
    elif "error" in result:
        error = result["error"]
        message = result.get("message", "N/A")
        
        print(f"\n❌ ERRO: {error}")
        print(f"   Mensagem: {message}")
        
        if error == "error_sign":
            print("\n💡 DICA: Assinatura HMAC incorreta")
            print("   Verifique se Partner Key está correta")
        elif error == "invalid_grant":
            print("\n💡 DICA: CODE expirou ou já foi usado")
            print("   Obtenha um novo CODE (códigos expiram em ~10 min)")
        elif error == "error_param":
            print("\n💡 DICA: Parâmetro faltando ou incorreto")
            print("   Verifique redirect_uri, shop_id, etc.")
    
except Exception as e:
    print(f"\n❌ ERRO: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "="*80)
