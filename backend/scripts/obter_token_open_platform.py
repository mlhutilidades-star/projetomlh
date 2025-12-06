#!/usr/bin/env python3
"""
Obter Shopee Access Token e Shop ID via Open Platform
Baseado na solução que funcionou no projeto MLH
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
    """Gerar assinatura HMAC SHA256 para Open Platform"""
    base_string = f"{PARTNER_ID}{path}{timestamp}"
    sign = hmac.new(
        partner_key.encode(),
        base_string.encode(),
        hashlib.sha256
    ).hexdigest()
    return sign

def main():
    print("\n" + "="*70)
    print("📱 SHOPEE OPEN PLATFORM - OBTER ACCESS TOKEN")
    print("="*70)
    
    print("\n🔗 PASSO 1: Clique neste link para AUTORIZAR:\n")
    
    auth_url = f"https://partner.shopeemobile.com/api/v2/oauth/authorize?partner_id={PARTNER_ID}&redirect_uri={REDIRECT_URI}&response_type=code&state=random_state_123"
    
    print(auth_url)
    
    print("\n" + "-"*70)
    print("Após autorizar, você será redirecionado para uma URL com o CODE")
    print("Procure por: ?code=XXXXX na URL de redirecionamento")
    print("-"*70)
    
    code = input("\n📋 Cole o CODE aqui (apenas a parte após 'code='): ").strip()
    
    if not code:
        print("❌ Código não fornecido")
        return
    
    # Remover 'code=' se o usuário colou com prefixo
    if code.startswith("code="):
        code = code[5:]
    
    print(f"\n✅ Código recebido: {code[:20]}...")
    
    print("\n" + "-"*70)
    print("🔄 PASSO 2: Trocando código pelo Access Token...")
    print("-"*70)
    
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
    
    try:
        # Endpoint da Open Platform (não Partner API)
        url = f"{SHOPEE_API}/auth/token/get"
        
        print(f"\n🔗 Endpoint: {url}")
        print(f"📊 Parâmetros: {json.dumps({k: v if k != 'code' else v[:20] + '...' for k, v in params.items()}, indent=2)}")
        
        response = requests.get(url, params=params, timeout=10)
        
        print(f"\n✅ Status Code: {response.status_code}")
        
        data = response.json()
        
        if "error" in data:
            print(f"\n❌ ERRO: {data['error']}")
            if "message" in data:
                print(f"   Mensagem: {data['message']}")
            return
        
        if "access_token" not in data:
            print(f"\n❌ Nenhum access token recebido")
            print(f"   Response: {json.dumps(data, indent=2)}")
            return
        
        access_token = data.get("access_token")
        refresh_token = data.get("refresh_token", "")
        expire_in = data.get("expire_in", 0)
        
        print(f"\n✅ Access Token obtido com sucesso!")
        print(f"   Expira em: {expire_in / 86400:.1f} dias")
        
        print("\n" + "-"*70)
        print("🏪 PASSO 3: Obtendo Shop ID...")
        print("-"*70)
        
        path_shop = "/shop/get_shop_info"
        sign_shop = generate_sign(path_shop, timestamp)
        
        shop_params = {
            "access_token": access_token,
            "timestamp": timestamp,
            "sign": sign_shop
        }
        
        shop_url = f"{SHOPEE_API}/shop/get_shop_info"
        shop_response = requests.get(shop_url, params=shop_params, timeout=10)
        shop_data = shop_response.json()
        
        print(f"\n✅ Status Code: {shop_response.status_code}")
        
        if "response" in shop_data:
            shop_id = shop_data["response"].get("shop_id")
            shop_name = shop_data["response"].get("shop_name")
            
            print(f"✅ Shop ID obtido com sucesso!")
            print(f"   Shop ID: {shop_id}")
            print(f"   Shop Name: {shop_name}")
            
        else:
            print(f"❌ Erro ao obter Shop ID")
            print(f"   Response: {json.dumps(shop_data, indent=2)}")
            return
        
        print("\n" + "="*70)
        print("✨ SUCESSO! COPIE ESTES VALORES PARA .env")
        print("="*70)
        
        print(f"\nSHOPEE_PARTNER_KEY={PARTNER_KEY}")
        print(f"SHOPEE_ACCESS_TOKEN={access_token}")
        print(f"SHOPEE_SHOP_ID={shop_id}")
        
        print("\n" + "-"*70)
        print("📝 PRÓXIMAS AÇÕES")
        print("-"*70)
        
        print("\n1. Abra: ap-gestor-saas/.env")
        
        print("\n2. Atualize as linhas:")
        print(f"   SHOPEE_PARTNER_KEY={PARTNER_KEY}")
        print(f"   SHOPEE_ACCESS_TOKEN={access_token}")
        print(f"   SHOPEE_SHOP_ID={shop_id}")
        
        print("\n3. Salve o arquivo")
        
        print("\n4. Execute a sincronização:")
        print("   docker-compose exec backend python scripts/sync_tiny_real.py")
        print("   docker-compose exec backend python scripts/sync_shopee_real.py")
        
        print("\n5. Acesse o dashboard:")
        print("   http://localhost:3000/dashboard")
        
        print("\n" + "="*70 + "\n")
        
    except requests.exceptions.Timeout:
        print("\n❌ ERRO: Timeout - API Shopee não respondeu")
    except requests.exceptions.ConnectionError:
        print("\n❌ ERRO: Sem conexão com a internet")
    except Exception as e:
        print(f"\n❌ ERRO: {e}")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n❌ Interrompido pelo usuário")
    except Exception as e:
        print(f"\n❌ Erro inesperado: {e}")
