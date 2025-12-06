#!/usr/bin/env python3
"""
Script simplificado para obter Shopee Access Token
Uso: python obter_access_token.py <PARTNER_KEY> <AUTH_CODE>
"""
import sys
import requests
import json

def obter_access_token(partner_key, auth_code):
    """Trocar authorization code por access token"""
    
    PARTNER_ID = "2013808"
    REDIRECT_URI = "https://irc-devoted-analysts-cst.trycloudflare.com/callback"
    
    print("\n" + "="*70)
    print("🔄 OBTENDO SHOPEE ACCESS TOKEN")
    print("="*70)
    
    print(f"\n📋 Parâmetros:")
    print(f"   Partner ID: {PARTNER_ID}")
    print(f"   Partner Key: {partner_key[:20]}...")
    print(f"   Auth Code: {auth_code[:20]}...")
    
    print("\n🔗 Enviando requisição para Shopee...")
    
    url = "https://partner.shopeemobile.com/api/v2/oauth/token"
    
    payload = {
        "code": auth_code,
        "grant_type": "authorization_code",
        "partner_id": PARTNER_ID,
        "partner_key": partner_key,
        "redirect_uri": REDIRECT_URI
    }
    
    try:
        response = requests.post(url, json=payload, timeout=10)
        
        print(f"Status Code: {response.status_code}")
        
        data = response.json()
        
        if response.status_code == 200 and "access_token" in data:
            print("\n✅ SUCESSO!")
            
            access_token = data.get("access_token")
            refresh_token = data.get("refresh_token")
            shop_id = data.get("shop_id")
            
            print("\n" + "="*70)
            print("📊 TOKENS GERADOS:")
            print("="*70)
            
            print(f"\nSHOPEE_ACCESS_TOKEN={access_token}")
            print(f"SHOPEE_SHOP_ID={shop_id}")
            
            if refresh_token:
                print(f"SHOPEE_REFRESH_TOKEN={refresh_token}")
            
            print("\n" + "-"*70)
            print("📝 PRÓXIMAS AÇÕES:")
            print("-"*70)
            
            print("\n1. Abra: ap-gestor-saas/.env")
            print("\n2. Preencha as linhas:")
            print(f"   SHOPEE_ACCESS_TOKEN={access_token}")
            print(f"   SHOPEE_SHOP_ID={shop_id}")
            
            print("\n3. Salve o arquivo")
            
            print("\n4. Execute a sincronização:")
            print("   docker-compose exec backend python scripts/sync_tiny_real.py")
            print("   docker-compose exec backend python scripts/sync_shopee_real.py")
            
            print("\n" + "="*70 + "\n")
            
        else:
            print(f"\n❌ ERRO: {data}")
            
            if "error_description" in data:
                print(f"Descrição: {data['error_description']}")
            
            if "error" in data:
                error = data["error"]
                if error == "invalid_grant":
                    print("→ Authorization code expirou (válido por ~10 minutos)")
                    print("→ Gere um novo code na URL OAuth")
                elif error == "invalid_client":
                    print("→ Partner ID ou Partner Key inválidos")
                elif error == "invalid_request":
                    print("→ Requisição malformada")
            
    except requests.exceptions.Timeout:
        print("❌ Timeout: API Shopee não respondeu")
    except Exception as e:
        print(f"❌ Erro: {e}")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("\n❌ USO INCORRETO\n")
        print("Sintaxe: python obter_access_token.py <PARTNER_KEY> <AUTH_CODE>\n")
        print("Exemplo:")
        print('python obter_access_token.py "shpk_abc123..." "code_xyz789..."\n')
        sys.exit(1)
    
    partner_key = sys.argv[1]
    auth_code = sys.argv[2]
    
    obter_access_token(partner_key, auth_code)
