#!/usr/bin/env python3
"""
Sincronização Shopee - VERSÃO REALISTA
- Funciona com os dados que a API realmente retorna
- Sem expectativas sobre campos que não existem
- Tratamento robusto de null/missing fields
"""
import os
import sys
import requests
import json
import hmac
import hashlib
import time
from datetime import datetime, timedelta
from pathlib import Path

from dotenv import load_dotenv
from shopee_token_manager import ensure_access_token, PARTNER_ID, PARTNER_KEY, SHOP_ID, BASE_URL

env_path = Path(__file__).parent.parent.parent / ".env"
load_dotenv(env_path)

# Obter token válido (refresh automático)
try:
    ACCESS_TOKEN = ensure_access_token()
except Exception as e:
    print(f"❌ Não foi possível obter access_token: {e}")
    print("➡️  Rode backend/scripts/obter_token_interativo_novo.py para reautorizar se necessário.")
    sys.exit(1)

def generate_sign(path: str, timestamp: int) -> str:
    """Gera assinatura HMAC-SHA256 com path incluindo /api/v2"""
    if not path.startswith("/api/v2"):
        path = f"/api/v2{path}"
    
    base_string = f"{PARTNER_ID}{path}{timestamp}{ACCESS_TOKEN}{SHOP_ID}"
    signature = hmac.new(
        PARTNER_KEY.encode(),
        base_string.encode(),
        hashlib.sha256
    ).hexdigest()
    return signature

def sync_products():
    """Sincronizar todos os produtos"""
    print("\n" + "="*70)
    print("🛍️  SINCRONIZANDO PRODUTOS")
    print("="*70)
    
    all_products = []
    offset = 0
    page_size = 50
    has_next = True
    
    # PASSO 1: Listar todos os product IDs
    print("\n📡 PASSO 1: Listando IDs de produtos...")
    
    while has_next:
        path = "/product/get_item_list"
        timestamp = int(time.time())
        sign = generate_sign(path, timestamp)
        
        params = {
            "partner_id": PARTNER_ID,
            "shop_id": SHOP_ID,
            "timestamp": timestamp,
            "access_token": ACCESS_TOKEN,
            "sign": sign,
            "offset": offset,
            "page_size": page_size,
            "item_status": "NORMAL"
        }
        
        url = BASE_URL + path
        resp = requests.get(url, params=params, timeout=10).json()
        
        if resp.get("error"):
            print(f"   ❌ Erro: {resp['error']}")
            break
        
        items = resp["response"]["item"]
        all_products.extend(items)
        
        print(f"   ✅ Batch {offset//page_size + 1}: {len(items)} produtos")
        
        has_next = resp["response"]["has_next_page"]
        offset = resp["response"].get("next_offset", offset + page_size)
        
        if has_next:
            time.sleep(1)  # Rate limit
    
    print(f"\n📊 Total de produtos encontrados: {len(all_products)}")
    
    # PASSO 2: Obter detalhes de todos
    print("\n📡 PASSO 2: Obtendo detalhes dos produtos...")
    
    product_details = []
    batch_size = 50  # Max items por requisição
    
    for i in range(0, len(all_products), batch_size):
        batch = all_products[i:i+batch_size]
        item_ids = [p["item_id"] for p in batch]
        
        path = "/product/get_item_base_info"
        timestamp = int(time.time())
        sign = generate_sign(path, timestamp)
        
        params = {
            "partner_id": PARTNER_ID,
            "shop_id": SHOP_ID,
            "timestamp": timestamp,
            "access_token": ACCESS_TOKEN,
            "sign": sign,
            "item_id_list": ",".join(str(id) for id in item_ids),
            "need_tax_info": "false",
            "need_complaint_policy": "false"
        }
        
        url = BASE_URL + path
        resp = requests.get(url, params=params, timeout=10).json()
        
        if resp.get("error"):
            print(f"   ❌ Erro: {resp['error']}")
            continue
        
        details = resp["response"]["item_list"]
        product_details.extend(details)
        
        print(f"   ✅ Batch {i//batch_size + 1}: {len(details)} produtos")
        
        if i + batch_size < len(all_products):
            time.sleep(1)  # Rate limit
    
    # PASSO 3: Normalizar e exibir
    print(f"\n📊 Total de detalhes obtidos: {len(product_details)}")
    print("\n📋 Amostra de produtos:")
    
    for idx, prod in enumerate(product_details[:5], 1):
        print(f"\n   {idx}. {prod.get('item_name', 'N/A')}")
        print(f"      Item ID: {prod['item_id']}")
        print(f"      SKU: {prod.get('item_sku', 'N/A')}")
        print(f"      Preço: R$ {prod.get('price', 'N/A')}")
        print(f"      Estoque: {prod.get('stock', 'N/A')}")
        
        # Se tem variantes
        if prod.get("has_model") and prod.get("model_list"):
            print(f"      Variantes: {len(prod['model_list'])}")
            for model in prod['model_list'][:2]:
                print(f"        - {model.get('model_name')} | SKU: {model.get('model_sku')} | Preço: {model.get('price')} | Estoque: {model.get('stock')}")
    
    return product_details

def sync_orders():
    """Sincronizar pedidos dos últimos 7 dias"""
    print("\n" + "="*70)
    print("📋 SINCRONIZANDO PEDIDOS")
    print("="*70)
    
    end_time = int(time.time())
    start_time = end_time - 7*24*60*60
    
    all_orders = []
    cursor = None
    has_more = True
    page = 1
    
    print(f"\n📡 Período: {datetime.fromtimestamp(start_time)} até {datetime.fromtimestamp(end_time)}")
    
    while has_more:
        path = "/order/get_order_list"
        timestamp = int(time.time())
        sign = generate_sign(path, timestamp)
        
        params = {
            "partner_id": PARTNER_ID,
            "shop_id": SHOP_ID,
            "timestamp": timestamp,
            "access_token": ACCESS_TOKEN,
            "sign": sign,
            "time_range_field": "create_time",
            "time_from": start_time,
            "time_to": end_time,
            "page_size": 50
        }
        
        if cursor:
            params["cursor"] = cursor
        
        url = BASE_URL + path
        resp = requests.get(url, params=params, timeout=10).json()
        
        if resp.get("error"):
            print(f"   ❌ Erro: {resp['error']}")
            break
        
        orders = resp["response"]["order_list"]
        all_orders.extend(orders)
        
        print(f"   ✅ Página {page}: {len(orders)} pedidos")
        
        has_more = resp["response"].get("more", False)
        cursor = resp["response"].get("next_cursor")
        page += 1
        
        if has_more:
            time.sleep(1)
    
    print(f"\n📊 Total de pedidos encontrados: {len(all_orders)}")
    print("\n📋 Amostra de pedidos:")
    
    for idx, order in enumerate(all_orders[:5], 1):
        print(f"\n   {idx}. Order SN: {order['order_sn']}")
        print(f"      Booking SN: {order.get('booking_sn', 'N/A')}")
    
    # NOTA: get_order_detail retorna error_not_found, então não conseguimos detalhes
    print("\n⚠️  Nota: get_order_detail não está acessível (error_not_found)")
    print("   Webhook ou outro método pode ser necessário para detalhes de pedidos")
    
    return all_orders

def main():
    print("="*70)
    print("🚀 SINCRONIZAÇÃO SHOPEE REALISTA")
    print("="*70)
    
    # Validar credenciais
    if not ACCESS_TOKEN:
        print("❌ ERRO: ACCESS_TOKEN não configurado")
        sys.exit(1)
    if not PARTNER_KEY:
        print("❌ ERRO: PARTNER_KEY não configurado")
        sys.exit(1)
    
    print(f"✅ Partner ID: {PARTNER_ID}")
    print(f"✅ Shop ID: {SHOP_ID}")
    print(f"✅ Access Token: {ACCESS_TOKEN[:10]}...")
    
    try:
        # Sincronizar produtos
        products = sync_products()
        
        # Sincronizar pedidos
        orders = sync_orders()
        
        print("\n" + "="*70)
        print("✅ SINCRONIZAÇÃO CONCLUÍDA")
        print("="*70)
        print(f"\n📊 Resumo:")
        print(f"   Produtos: {len(products)}")
        print(f"   Pedidos: {len(orders)}")
        print(f"\n💡 Próximos passos:")
        print(f"   1. Normalizar dados obtidos")
        print(f"   2. Inserir em PostgreSQL")
        print(f"   3. Configurar webhooks para pedidos")
        
    except Exception as e:
        print(f"\n❌ ERRO: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
