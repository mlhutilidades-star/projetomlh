#!/usr/bin/env python3
"""
Obter Shopee Access Token - VERSÃO CORRIGIDA COM QUERY PARAMS
Baseado na solução do projeto MLH - Corrigindo formato de requisição
"""
import requests
import json
import time
import hmac
import hashlib
import webbrowser
from urllib.parse import urlencode

PARTNER_ID = "2013808"
PARTNER_KEY = "shpk4774635844546f67744c5150584a6e554b454f4a576c514b65734c664952"
REDIRECT_URI = "https://irc-devoted-analysts-cst.trycloudflare.com/callback"
SHOPEE_API = "https://partner.shopeemobile.com/api/v2"

def generate_sign(path: str, timestamp: int, partner_key: str = PARTNER_KEY) -> str:
    """Gerar assinatura HMAC SHA256 para Open Platform"""
    base_string = f"{PARTNER_ID}{path}{timestamp}"
    sign = hmac.new(
        partner_key.encode(),
        base_string.encode(),
        hashlib.sha256
    ).hexdigest()
    print(f"  [DEBUG] Base string: {base_string}")
    print(f"  [DEBUG] Sign: {sign}")
    return sign

def main():
    print("\n" + "="*80)
    print("🚀 SHOPEE OPEN PLATFORM - OBTER ACCESS TOKEN (VERSÃO INTERATIVA)")
    print("="*80)
    
    # PASSO 1: Mostrar URL de autorização
    print("\n✅ PASSO 1: AUTORIZAR NO SHOPEE")
    print("-" * 80)
    
    state = "random_state_123"
    auth_params = {
        "partner_id": PARTNER_ID,
        "redirect_uri": REDIRECT_URI,
        "response_type": "code",
        "state": state
    }
    
    auth_url = f"{SHOPEE_API}/oauth/authorize?" + urlencode(auth_params)
    
    print(f"\n📋 URL DE AUTORIZAÇÃO:\n")
    print(auth_url)
    print(f"\n💡 COPIE a URL acima e cole no navegador")
    print(f"\n⚠️  Após clicar em 'Autorizar', você será redirecionado para:")
    print(f"   https://irc-devoted-analysts-cst.trycloudflare.com?code=XXXXX&state={state}")
    
    # Perguntar se quer abrir no navegador automaticamente
    open_browser = input(f"\n🌐 Abrir no navegador automaticamente? (s/n): ").strip().lower()
    if open_browser == 's':
        webbrowser.open(auth_url)
        print("✅ Navegador aberto! Autorize e aguarde a redireção...")
    
    # PASSO 2: Receber o CODE
    print("\n\n✅ PASSO 2: COPIAR O CODE")
    print("-" * 80)
    print("\n📍 Após autorizar, procure na URL por: ?code=CODE_AQUI&state=...")
    print("\n⏱️  O CODE tem a forma: code_xxxxxxxxxxxxxxxx")
    
    code = input("\n📋 Cole o CODE COMPLETO (code_xxxxx...): ").strip()
    
    if not code:
        print("❌ Código não fornecido!")
        return False
    
    # Limpar o código se necessário
    if code.startswith("code="):
        code = code[5:]  # Remove "code="
    
    print(f"\n✅ Código recebido: {code[:50]}...")
    
    # PASSO 3: Trocar code por access token
    print("\n\n✅ PASSO 3: TROCAR CODE POR ACCESS TOKEN")
    print("-" * 80)
    
    timestamp = int(time.time())
    path = "/auth/token/get"
    sign = generate_sign(path, timestamp)
    
    # Parâmetros como QUERY STRING (não JSON)
    token_params = {
        "partner_id": PARTNER_ID,
        "code": code,
        "grant_type": "authorization_code",
        "redirect_uri": REDIRECT_URI,
        "timestamp": timestamp,
        "sign": sign
    }
    
    print(f"\n🔗 Endpoint: {SHOPEE_API}{path}")
    print(f"\n📊 Parâmetros (Query String):")
    print(json.dumps(token_params, indent=2))
    
    print(f"\n⏳ Aguardando resposta do Shopee...")
    
    try:
        # Requisição GET com query parameters (não POST com JSON)
        response = requests.get(
            f"{SHOPEE_API}{path}",
            params=token_params,
            timeout=10
        )
        
        print(f"\n📊 Status: {response.status_code}")
        print(f"📄 Resposta:\n{json.dumps(response.json(), indent=2, ensure_ascii=False)}")
        
        result = response.json()
        
        if "access_token" in result:
            print("\n\n" + "="*80)
            print("🎉 SUCESSO! TOKENS OBTIDOS!")
            print("="*80)
            
            access_token = result.get("access_token")
            shop_id = result.get("shop_id")
            refresh_token = result.get("refresh_token", "")
            expire_in = result.get("expire_in", "")
            
            print(f"\n✅ Access Token: {access_token}")
            print(f"✅ Shop ID: {shop_id}")
            if refresh_token:
                print(f"✅ Refresh Token: {refresh_token}")
            if expire_in:
                print(f"✅ Expira em: {expire_in} segundos (~{expire_in//3600} horas)")
            
            print("\n\n📝 COPIE ISSO PARA SEU .env:")
            print("-" * 80)
            print(f'SHOPEE_ACCESS_TOKEN="{access_token}"')
            print(f"SHOPEE_SHOP_ID={shop_id}")
            if refresh_token:
                print(f'SHOPEE_REFRESH_TOKEN="{refresh_token}"')
            print("-" * 80)
            
            return True
        else:
            error = result.get('error', 'Erro desconhecido')
            message = result.get('error_description', result.get('message', 'N/A'))
            print(f"\n❌ ERRO: {error}")
            print(f"   Mensagem: {message}")
            
            # Dicas de troubleshooting
            if error == "error_not_found":
                print("\n💡 DICA: Erro 'error_not_found' geralmente significa:")
                print("   - O CODE está expirado (válido por ~10 min)")
                print("   - O CODE é inválido ou mal formatado")
                print("   - Tente obter um novo CODE")
            elif error == "error_param":
                print("\n💡 DICA: Erro 'error_param' significa parâmetro faltando ou inválido")
            elif error == "error_sign":
                print("\n💡 DICA: Erro 'error_sign' significa assinatura HMAC incorreta")
            
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"\n❌ ERRO DE CONEXÃO: {e}")
        return False

if __name__ == "__main__":
    success = main()
    print("\n" + "="*80)
    if success:
        print("✅ Processo concluído com SUCESSO!")
    else:
        print("❌ Processo falhou. Verifique os erros acima.")
    print("="*80 + "\n")
