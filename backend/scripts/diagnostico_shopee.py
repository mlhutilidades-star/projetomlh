#!/usr/bin/env python3
"""
Testar e diagnosticar erro com Shopee API
"""
import requests
import json
import hmac
import hashlib
import time

PARTNER_ID = "2013808"
PARTNER_KEY = "shpk4774635844546f67744c5150584a6e554b454f4a576c514b65734c664952"

def shopee_sign(path: str, timestamp: int) -> str:
    """Gerar assinatura HMAC para Shopee API"""
    base_string = f"{PARTNER_ID}{path}{timestamp}"
    signature = hmac.new(
        PARTNER_KEY.encode(),
        base_string.encode(),
        hashlib.sha256
    ).hexdigest()
    return signature

def test_shopee_connection():
    print("\n" + "="*70)
    print("🔍 DIAGNÓSTICO SHOPEE API")
    print("="*70)
    
    print("\n📋 Credenciais Configuradas:")
    print(f"   Partner ID: {PARTNER_ID}")
    print(f"   Partner Key: {PARTNER_KEY[:30]}...")
    
    # Teste 1: Verificar se os credentials são válidos
    print("\n" + "-"*70)
    print("TESTE 1: Validar Partner ID e Partner Key")
    print("-"*70)
    
    timestamp = int(time.time())
    path = "/api/v2/auth_partner"
    sign = shopee_sign(path, timestamp)
    
    url = f"https://partner.shopeemobile.com{path}"
    params = {
        "partner_id": PARTNER_ID,
        "timestamp": timestamp,
        "sign": sign
    }
    
    try:
        resp = requests.get(url, params=params, timeout=10)
        print(f"Status Code: {resp.status_code}")
        
        if resp.status_code == 200:
            print("✅ Partner ID e Partner Key são VÁLIDOS")
        elif resp.status_code == 403:
            print("❌ ERRO 403: Não autorizado")
            print("   → Partner ID ou Partner Key incorretos")
            print("   → IP da máquina pode estar bloqueado")
        elif resp.status_code == 404:
            print("⚠️  ERRO 404: Endpoint não encontrado")
        else:
            print(f"❌ ERRO: {resp.text[:200]}")
            
    except Exception as e:
        print(f"❌ Erro de conexão: {e}")
    
    # Teste 2: Tentar obter informações da aplicação
    print("\n" + "-"*70)
    print("TESTE 2: Obter informações da aplicação")
    print("-"*70)
    
    path = "/api/v2/shop/get_partner_shop"
    sign = shopee_sign(path, timestamp)
    
    url = f"https://partner.shopeemobile.com{path}"
    params = {
        "partner_id": PARTNER_ID,
        "timestamp": timestamp,
        "sign": sign
    }
    
    try:
        resp = requests.get(url, params=params, timeout=10)
        print(f"Status Code: {resp.status_code}")
        
        if resp.status_code == 200:
            data = resp.json()
            print("✅ Consegui obter dados da aplicação")
            print(json.dumps(data, indent=2, ensure_ascii=False)[:500])
        else:
            print(f"❌ ERRO {resp.status_code}")
            print(f"Response: {resp.text[:300]}")
            
    except Exception as e:
        print(f"❌ Erro: {e}")
    
    # Teste 3: Sugestões
    print("\n" + "-"*70)
    print("🔧 SOLUÇÕES POSSÍVEIS")
    print("-"*70)
    
    print("\n❌ Se você recebeu 'error_not_found', verifique:")
    print("\n1. **Partner ID está correto?**")
    print("   → Acesse: https://seller.shopee.com.br/api")
    print("   → Vá para: Settings > App Center")
    print("   → Copie o Partner ID exato (sem espaços)")
    
    print("\n2. **Partner Key está correto?**")
    print("   → No mesmo local, verifique a Partner Key")
    print("   → Deve começar com 'shpk...'")
    print("   → Copie SEM espaços")
    
    print("\n3. **Access Token já foi gerado?**")
    print("   → Você precisa primeiro autorizar a aplicação via OAuth")
    print("   → Depois terá um Access Token")
    
    print("\n4. **Seu IP está whitelistado?**")
    print("   → Shopee pode bloquear por restrição de IP")
    print("   → Verifique nas configurações de segurança")
    
    print("\n" + "="*70)
    print("📝 PRÓXIMAS AÇÕES")
    print("="*70)
    
    print("\n1. Verifique se os valores copiados estão CORRETOS")
    print("   → Acesse: https://seller.shopee.com.br/api")
    print("   → Settings > App Center > Copie valores exatos")
    
    print("\n2. Se tudo estiver certo, tente novamente")
    print("   → python backend/scripts/obter_shopee_tokens.py")
    
    print("\n3. Se continuar erro, use a URL diretamente:")
    print("   → https://partner.shopeemobile.com/api/v2/oauth/authorize?")
    print("     client_id=2013808&response_type=code&")
    print("     redirect_uri=http://localhost:8888/callback")
    
    print("\n" + "="*70 + "\n")

if __name__ == "__main__":
    test_shopee_connection()
