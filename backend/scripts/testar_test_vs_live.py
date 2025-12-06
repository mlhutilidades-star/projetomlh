#!/usr/bin/env python3
"""
Testar com AMBOS os Partner IDs: TEST (1198503) e LIVE (2013808)
Baseado na imagem do Shopee Developer Portal
"""
import requests
import json
import time
import hmac
import hashlib

# Configurações
CONFIGS = {
    "TEST": {
        "partner_id": "1198503",
        "partner_key": "",  # PRECISA PREENCHER
        "redirect_uri": "https://irc-devoted-analysts-cst.trycloudflare.com",
        "shop_id": "1198503"  # Do .env.local do PROJETO MLH
    },
    "LIVE": {
        "partner_id": "2013808",
        "partner_key": "shpk4774635844546f67744c5150584a6e554b454f4a576c514b65734c664952",
        "redirect_uri": "https://irc-devoted-analysts-cst.trycloudflare.com",
        "shop_id": ""  # NÃO TEMOS AINDA
    }
}

SHOPEE_API = "https://partner.shopeemobile.com/api/v2"

def generate_sign(partner_id: str, path: str, timestamp: int, partner_key: str) -> str:
    """Gerar assinatura HMAC SHA256"""
    base_string = f"{partner_id}{path}{timestamp}"
    sign = hmac.new(
        partner_key.encode(),
        base_string.encode(),
        hashlib.sha256
    ).hexdigest()
    return sign

print("\n" + "="*80)
print("🔍 TESTANDO AMBOS PARTNER IDs: TEST vs LIVE")
print("="*80)

for env_name, config in CONFIGS.items():
    print(f"\n\n{'='*80}")
    print(f"🧪 TESTANDO: {env_name}")
    print(f"{'='*80}")
    
    partner_id = config["partner_id"]
    partner_key = config["partner_key"]
    redirect_uri = config["redirect_uri"]
    shop_id = config.get("shop_id", "")
    
    print(f"\n📊 Configuração:")
    print(f"   Partner ID: {partner_id}")
    print(f"   Partner Key: {'***' + partner_key[-10:] if partner_key else 'NÃO CONFIGURADO'}")
    print(f"   Shop ID: {shop_id if shop_id else 'DESCONHECIDO'}")
    
    if not partner_key:
        print(f"\n⚠️  Partner Key não configurado para {env_name}")
        print(f"   Pule ou configure no código")
        continue
    
    # TESTE 1: URL de Autorização
    print(f"\n\n📋 TESTE 1: URL DE AUTORIZAÇÃO")
    print("-" * 80)
    
    auth_url = f"{SHOPEE_API}/oauth/authorize?partner_id={partner_id}&redirect_uri={redirect_uri}&response_type=code&state=test_{env_name}"
    print(f"\n🔗 URL: {auth_url}")
    
    try:
        response = requests.head(auth_url, allow_redirects=False, timeout=5)
        print(f"   Status: {response.status_code}")
        if response.status_code == 404:
            print(f"   ❌ error_not_found - Partner ID não registrado")
        elif response.status_code in [301, 302, 307]:
            print(f"   ✅ Redirect OK - Partner funciona!")
    except Exception as e:
        print(f"   Erro: {str(e)[:100]}")
    
    # TESTE 2: Se temos shop_id, tentar obter info
    if shop_id:
        print(f"\n\n📋 TESTE 2: GET SHOP INFO (com shop_id)")
        print("-" * 80)
        
        timestamp = int(time.time())
        path = "/shop/get_shop_info"
        sign = generate_sign(partner_id, path, timestamp, partner_key)
        
        params = {
            "partner_id": partner_id,
            "shop_id": shop_id,
            "timestamp": timestamp,
            "sign": sign
        }
        
        try:
            response = requests.get(
                f"{SHOPEE_API}{path}",
                params=params,
                timeout=5
            )
            print(f"   Status: {response.status_code}")
            result = response.json()
            
            if "error" in result:
                print(f"   Error: {result['error']}")
                print(f"   Message: {result.get('message', 'N/A')}")
            else:
                print(f"   ✅ RESPOSTA:")
                print(f"   {json.dumps(result, indent=6)[:500]}")
        except Exception as e:
            print(f"   Erro: {str(e)[:100]}")
    
    # TESTE 3: Tentar autorização MANUAL
    print(f"\n\n📋 TESTE 3: AUTORIZAÇÃO MANUAL")
    print("-" * 80)
    print(f"\n💡 Para testar {env_name} Partner:")
    print(f"\n1. Cole no navegador:")
    print(f"   {auth_url}")
    print(f"\n2. Se funcionar, você verá página de login/autorização Shopee")
    print(f"3. Após autorizar, copie o CODE da URL")
    print(f"4. Use o CODE para obter access_token")

print("\n\n" + "="*80)
print("💡 CONCLUSÕES E PRÓXIMOS PASSOS")
print("="*80)

print("""
1. Se TEST funcionar e LIVE não:
   → Use ambiente TEST para desenvolvimento
   → Solicite ativação do LIVE no Shopee

2. Se LIVE funcionar:
   → Obtenha CODE da URL de autorização
   → Troque CODE por access_token
   → Obtenha shop_id da resposta

3. Se NENHUM funcionar:
   → Partner IDs podem não estar registrados
   → Verifique Shopee Developer Portal
   → Copie Partner Key corretamente (pode ter expirado)

4. Próximo passo: Obter TEST Partner Key
   → Acesse Shopee Developer Portal
   → Copie "Test API Partner Key"
   → Atualize no código acima
   → Rode novamente
""")

print("="*80)
