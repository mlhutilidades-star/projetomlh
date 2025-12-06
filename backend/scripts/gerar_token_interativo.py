#!/usr/bin/env python3
"""
Script interativo para obter Shopee Access Token
Segue passo a passo com você
"""
import requests
import json
import webbrowser
import time

PARTNER_ID = "2013808"
REDIRECT_URL = "https://irc-devoted-analysts-cst.trycloudflare.com/callback"

def main():
    print("\n" + "="*70)
    print("🔐 GERADOR INTERATIVO - SHOPEE ACCESS TOKEN")
    print("="*70)
    
    print("\n📋 PRÉ-REQUISITOS:")
    print("   ✅ Partner ID: 2013808")
    print("   ⚠️  Você precisa ter:")
    print("      - Live API Partner Key (completa)")
    print("      - Authorization Code (gerado via OAuth)")
    
    print("\n" + "-"*70)
    print("PASSO 1: OBTER AUTHORIZATION CODE")
    print("-"*70)
    
    print("\n🔗 URL de autorização:")
    oauth_url = f"https://partner.shopeemobile.com/api/v2/oauth/authorize?client_id={PARTNER_ID}&response_type=code&redirect_uri={REDIRECT_URL}&state=state123"
    print(f"\n{oauth_url}\n")
    
    print("📋 INSTRUÇÕES:")
    print("1. Copie a URL acima")
    print("2. Cole no navegador e pressione ENTER")
    print("3. Faça login no Shopee (se solicitado)")
    print("4. Clique em 'Autorizar'")
    print("5. Procure por 'code=XXXXX' na URL de redirecionamento")
    print("6. Copie o código completo (incluindo 'code=')")
    
    print("\n" + "-"*70)
    print("PASSO 2: INFORMAÇÕES NECESSÁRIAS")
    print("-"*70)
    
    # Input 1: Partner Key
    print("\n1️⃣  PARTNER KEY (Live)")
    print("   ℹ️  Acesse: https://seller.shopee.com.br/api/setting/partner-development")
    print("   ℹ️  Clique no olho para revelar a 'Live API Partner Key'")
    print("   ℹ️  Clique em Copiar")
    
    partner_key = input("\n   Cole a Live API Partner Key: ").strip()
    
    if not partner_key or len(partner_key) < 10:
        print("   ❌ Partner Key inválida (muito curta)")
        return
    
    print(f"   ✅ Recebido: {partner_key[:30]}...")
    
    # Input 2: Authorization Code
    print("\n2️⃣  AUTHORIZATION CODE")
    print("   ℹ️  Após autorizar no Shopee, você será redirecionado")
    print("   ℹ️  Procure na URL por: code=XXXXX")
    print("   ℹ️  Cole o código completo (ou apenas a parte após 'code=')")
    
    auth_code = input("\n   Cole o Authorization Code: ").strip()
    
    if not auth_code or len(auth_code) < 5:
        print("   ❌ Authorization Code inválido")
        return
    
    # Remover 'code=' se o usuário colou a parte inteira
    if auth_code.startswith("code="):
        auth_code = auth_code[5:]
    
    print(f"   ✅ Recebido: {auth_code[:30]}...")
    
    # Trocar code por token
    print("\n" + "-"*70)
    print("PASSO 3: GERANDO ACCESS TOKEN")
    print("-"*70)
    
    print("\n🔄 Enviando requisição para Shopee...")
    
    url = "https://partner.shopeemobile.com/api/v2/oauth/token"
    payload = {
        "code": auth_code,
        "grant_type": "authorization_code",
        "partner_id": PARTNER_ID,
        "partner_key": partner_key,
        "redirect_uri": REDIRECT_URL
    }
    
    try:
        response = requests.post(url, json=payload, timeout=10)
        data = response.json()
        
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200 and "access_token" in data:
            print("✅ SUCESSO!\n")
            
            access_token = data.get("access_token")
            shop_id = data.get("shop_id")
            refresh_token = data.get("refresh_token")
            
            print("="*70)
            print("✨ TOKENS GERADOS COM SUCESSO!")
            print("="*70)
            
            print(f"\n🔑 Access Token:")
            print(f"   {access_token}")
            
            print(f"\n🏪 Shop ID:")
            print(f"   {shop_id}")
            
            if refresh_token:
                print(f"\n🔄 Refresh Token:")
                print(f"   {refresh_token}")
            
            # Salvar no .env
            print("\n" + "="*70)
            print("📝 ATUALIZAR .env")
            print("="*70)
            
            print("\n✏️  Abra: ap-gestor-saas/.env")
            print("\nE atualize estas linhas:")
            print(f"SHOPEE_PARTNER_KEY={partner_key}")
            print(f"SHOPEE_ACCESS_TOKEN={access_token}")
            print(f"SHOPEE_SHOP_ID={shop_id}")
            
            print("\n" + "="*70)
            print("🚀 PRÓXIMAS AÇÕES")
            print("="*70)
            
            print("\n1. Salve o arquivo .env")
            
            print("\n2. Execute a sincronização:")
            print("   docker-compose exec backend python scripts/sync_tiny_real.py")
            print("   docker-compose exec backend python scripts/sync_shopee_real.py")
            
            print("\n3. Acesse o dashboard:")
            print("   http://localhost:3000/dashboard")
            
            print("\n" + "="*70 + "\n")
            
        else:
            print(f"\n❌ ERRO: {data}\n")
            
            if "error" in data:
                error = data["error"]
                print(f"Código de erro: {error}")
                
                if error == "invalid_grant":
                    print("❌ Authorization Code expirou ou é inválido")
                    print("   → Os codes são válidos por ~10 minutos")
                    print("   → Gere um novo code na URL OAuth")
                
                elif error == "invalid_client":
                    print("❌ Partner ID ou Partner Key inválidos")
                    print("   → Verifique se copiou corretamente")
                    print("   → Sem espaços ou caracteres extras")
                
                elif error == "invalid_request":
                    print("❌ Requisição malformada")
                    print("   → Verifique os parâmetros enviados")
            
            if "error_description" in data:
                print(f"Detalhes: {data['error_description']}")
    
    except requests.exceptions.Timeout:
        print("\n❌ ERRO: Timeout - API Shopee não respondeu")
        print("   → Tente novamente")
    
    except requests.exceptions.ConnectionError:
        print("\n❌ ERRO: Sem conexão com a internet")
        print("   → Verifique sua conexão")
    
    except Exception as e:
        print(f"\n❌ ERRO: {e}")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n❌ Interrompido pelo usuário")
    except Exception as e:
        print(f"\n❌ Erro inesperado: {e}")
