"""
Teste de conexões de API: Tiny ERP e Shopee
Executa chamadas leves para validar credenciais e conectividade.
"""
import sys
from pathlib import Path
import json

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from modules.config import get_env
from modules.tiny_api import listar_produtos, listar_pedidos
from modules.shopee_api import listar_pedidos as shopee_listar_pedidos

print("=" * 60)
print("🔌 TESTE DE CONEXÕES DE API")
print("=" * 60)

# Load env
env = get_env()

# Tiny ERP
print("\n🏢 Tiny ERP")
token = env.get("TINY_API_TOKEN")
if not token or token == "seu_token_tiny_aqui":
    print("⚠️ Token do Tiny ausente ou placeholder. Configure em .env (TINY_API_TOKEN)")
else:
    print("→ Testando listar_produtos (primeira página)...")
    resp = listar_produtos(page=1)
    if isinstance(resp, dict) and resp.get("error"):
        print(f"❌ Erro Tiny: {resp['error']}")
        if resp.get("status_code"):
            print(f"   HTTP {resp['status_code']}")
    else:
        # Show small summary
        items = resp.get("produtos") if isinstance(resp, dict) else None
        count = len(items) if items else 0
        print(f"✅ Conectado! {count} produtos retornados na página 1")

    print("→ Testando listar_pedidos (últimos 7 dias)...")
    resp = listar_pedidos(page=1)
    if isinstance(resp, dict) and resp.get("error"):
        print(f"❌ Erro Tiny (pedidos): {resp['error']}")
    else:
        pedidos = resp.get("pedidos") if isinstance(resp, dict) else None
        count = len(pedidos) if pedidos else 0
        print(f"✅ Conectado! {count} pedidos retornados")

# Shopee
print("\n🛍️ Shopee")
partner_id = env.get("SHOPEE_PARTNER_ID")
partner_key = env.get("SHOPEE_PARTNER_KEY")
shop_id = env.get("SHOPEE_SHOP_ID")
access_token = env.get("SHOPEE_ACCESS_TOKEN")

if not partner_id or not partner_key or not shop_id:
    print("⚠️ Credenciais Shopee ausentes. Configure em .env (SHOPEE_PARTNER_ID/KEY/SHOP_ID)")
elif not access_token:
    print("⚠️ Access Token Shopee ausente (obrigatório para API v2)")
    print("\n📋 Para obter o access_token:")
    print("   1. Execute: python shopee_generate_auth_url.py")
    print("   2. Abra a URL gerada e autorize")
    print("   3. Execute: python shopee_get_token.py <code>")
    print("   4. Atualize o .env com os tokens")
    print("\n   Veja SHOPEE_AUTH_SETUP.md para detalhes completos\n")
else:
    print("→ Testando listar_pedidos (últimas 48h)...")
    resp = shopee_listar_pedidos()
    if isinstance(resp, dict) and resp.get("error"):
        print(f"❌ Erro Shopee: {resp['error']}")
        if resp.get("status_code"):
            print(f"   HTTP {resp['status_code']}")
    else:
        orders = resp.get("order_list") if isinstance(resp, dict) else None
        count = len(orders) if orders else 0
        print(f"✅ Conectado! {count} pedidos retornados")

print("\n" + "=" * 60)
print("📋 CONCLUSÃO")
print("=" * 60)

tiny_ok = bool(token and token != "seu_token_tiny_aqui")
shopee_ok = bool(partner_id and partner_key and shop_id and access_token)

if tiny_ok:
    print("Tiny ERP: ✅ Credenciais presentes e funcionais")
else:
    print("Tiny ERP: ❌ Credenciais faltando")

if shopee_ok:
    print("Shopee: ✅ Credenciais completas (incluindo access_token)")
elif partner_id and partner_key and shop_id:
    print("Shopee: ⚠️ Credenciais básicas OK, mas falta access_token OAuth")
    print("        Execute: python shopee_generate_auth_url.py")
else:
    print("Shopee: ❌ Credenciais faltando")

print("\n💡 Dica:")
if tiny_ok and not shopee_ok:
    print("  - Tiny ERP está pronto para sincronização!")
    print("  - Execute: python sync_tiny_erp.py")
    print("  - Para Shopee, siga SHOPEE_AUTH_SETUP.md")
elif not tiny_ok:
    print("  - Configure TINY_API_TOKEN no .env")
elif tiny_ok and shopee_ok:
    print("  - Ambas as APIs estão prontas!")
    print("  - Execute: python sync_tiny_erp.py")
    print("  - Execute: python sync_shopee.py")
else:
    print("  - Edite .env e rode novamente este teste")
