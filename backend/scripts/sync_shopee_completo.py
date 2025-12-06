#!/usr/bin/env python3
"""
Sincronização Completa Shopee Open Platform API v2
- Lista de produtos com paginação
- Detalhes de produtos
- Lista de pedidos com filtro de tempo
- Detalhes de pedidos com itens

Fórmula HMAC-SHA256 CORRETA: {partner_id}{path}{timestamp}{access_token}{shop_id}
"""
import os
import sys
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

# Obter token válido (faz refresh se necessário)
try:
    ACCESS_TOKEN = ensure_access_token()
except Exception as e:
    print(f"❌ Não foi possível obter access_token: {e}")
    print("➡️  Rode backend/scripts/obter_token_interativo_novo.py para reautorizar se o refresh falhar.")
    sys.exit(1)

print(f"✅ Partner ID: {PARTNER_ID}, Shop ID: {SHOP_ID}")
print(f"✅ Access Token carregado (cache/refresh): {ACCESS_TOKEN[:10]}...")
def generate_sign(path: str, timestamp: int) -> str:
    """
    Gera assinatura HMAC-SHA256
    Fórmula TESTADA E COMPROVADA: {partner_id}{path}{timestamp}{access_token}{shop_id}
    
    IMPORTANTE: O path deve incluir /api/v2
    """
    # Garantir que o path começa com /api/v2
    if not path.startswith("/api/v2"):
        path = f"/api/v2{path}"
    
    base_string = f"{PARTNER_ID}{path}{timestamp}{ACCESS_TOKEN}{SHOP_ID}"
    
    signature = hmac.new(
        PARTNER_KEY.encode(),
        base_string.encode(),
        hashlib.sha256
    ).hexdigest()
    
    return signature

def get_products(offset=0, page_size=50, item_status="NORMAL"):
    """
    Lista produtos com paginação
    """
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
        "item_status": item_status
    }
    
    url = BASE_URL + path  # Usar + em vez de f-string para evitar duplicação
    print(f"\n📡 GET {url}")
    print(f"   Params: offset={offset}, page_size={page_size}, status={item_status}")
    
    response = requests.get(url, params=params, timeout=10)
    data = response.json()
    
    print(f"   Status: {response.status_code}")
    if data.get("error"):
        print(f"   ❌ Error: {data['error']} - {data.get('message', '')}")
        return None
    
    print(f"   ✅ Sucesso! {len(data['response']['item'])} produtos")
    print(f"   Total: {data['response']['total_count']}, Has next: {data['response']['has_next_page']}")
    
    return data["response"]

def get_product_details(item_ids: list):
    """
    Obter detalhes de produtos específicos (SKU, preço, estoque, etc)
    """
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
    print(f"\n📡 GET {url}")
    print(f"   Buscando detalhes de {len(item_ids)} produtos")
    
    response = requests.get(url, params=params, timeout=10)
    data = response.json()
    
    print(f"   Status: {response.status_code}")
    if data.get("error"):
        print(f"   ❌ Error: {data['error']} - {data.get('message', '')}")
        return None
    
    print(f"   ✅ Sucesso! Detalhes recebidos")
    
    return data["response"]["item_list"]

def get_orders(time_from, time_to, page_size=50, cursor=None):
    """
    Lista pedidos em intervalo de tempo
    Intervalo máximo: 15 dias (1296000 segundos)
    """
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
        "time_from": time_from,
        "time_to": time_to,
        "page_size": page_size
    }
    
    if cursor:
        params["cursor"] = cursor
    
    url = BASE_URL + path
    print(f"\n📡 GET {url}")
    print(f"   Intervalo: {datetime.fromtimestamp(time_from)} até {datetime.fromtimestamp(time_to)}")
    print(f"   Tamanho: {time_to - time_from} segundos")
    
    response = requests.get(url, params=params, timeout=10)
    data = response.json()
    
    print(f"   Status: {response.status_code}")
    if data.get("error"):
        print(f"   ❌ Error: {data['error']} - {data.get('message', '')}")
        return None
    
    print(f"   ✅ Sucesso! {len(data['response']['order_list'])} pedidos")
    print(f"   Total na faixa: {data['response'].get('total_count', '?')}, Has more: {data['response'].get('more', False)}")
    
    return data["response"]


def fetch_all_orders(time_from, time_to, page_size=50):
    """
    Percorre todas as páginas de pedidos no intervalo informado (limite Shopee: 15 dias)
    usando cursor até que "more" seja False.
    """
    all_orders = []
    cursor = None
    page = 1
    while True:
        resp = get_orders(time_from, time_to, page_size=page_size, cursor=cursor)
        if not resp:
            break
        batch = resp.get("order_list", [])
        all_orders.extend(batch)
        print(f"   ✅ Página {page}: +{len(batch)} (total {len(all_orders)})")
        if not resp.get("more"):
            break
        cursor = resp.get("next_cursor")
        page += 1
        time.sleep(0.8)
    return all_orders

def get_order_details(order_sn_list):
    """
    Obter detalhes completos de pedidos (itens, preços, endereço, etc)
    """
    path = "/order/get_order_detail"
    timestamp = int(time.time())
    sign = generate_sign(path, timestamp)
    
    # Para evitar erros de not_found, envie como string separada por vírgula (formato aceito pela API)
    order_sn_str = ",".join(order_sn_list)
    
    params = {
        "partner_id": PARTNER_ID,
        "shop_id": SHOP_ID,
        "timestamp": timestamp,
        "access_token": ACCESS_TOKEN,
        "sign": sign,
        "order_sn_list": order_sn_str,
        "response_optional_fields": ",".join([
            "order_status", "buyer_username", "recipient_address", "item_list",
            "payment_method", "estimated_shipping_fee", "actual_shipping_fee",
            "total_amount", "cancel_by", "cancel_reason", "note", "package_list"
        ])
    }
    
    url = BASE_URL + path
    print(f"\n📡 GET {url}")
    print(f"   Buscando detalhes de {len(order_sn_list)} pedidos")
    
    response = requests.get(url, params=params, timeout=10)
    data = response.json()
    
    print(f"   Status: {response.status_code}")
    if data.get("error"):
        print(f"   ❌ Error: {data['error']} - {data.get('message', '')}")
        return None
    
    print(f"   ✅ Sucesso! Detalhes recebidos")
    
    return data["response"]["order_list"]

def main():
    print("="*70)
    print("🛍️ SINCRONIZAÇÃO SHOPEE - COMPLETA")
    print("="*70)
    
    # ===== PRODUTOS =====
    print("\n\n📦 PASSO 1: LISTAR PRODUTOS")
    print("-"*70)
    
    products_resp = get_products(offset=0, page_size=10, item_status="NORMAL")
    if not products_resp:
        print("❌ Falha ao obter produtos. Abortando.")
        return
    
    product_list = products_resp["item"]
    total_products = products_resp["total_count"]
    
    print(f"\n📊 Total de produtos no shop: {total_products}")
    print(f"📋 Primeiros {len(product_list)} produtos:")
    
    for idx, prod in enumerate(product_list, 1):
        name = prod.get('item_name', prod.get('title', 'N/A'))
        status = prod.get('item_status', 'N/A')
        item_id = prod.get('item_id', 'N/A')
        print(f"   {idx}. Item ID: {item_id}, Status: {status}, Nome: {name}")
    
    # ===== DETALHES DE PRODUTOS =====
    print("\n\n📄 PASSO 2: OBTER DETALHES DE PRODUTOS")
    print("-"*70)
    
    item_ids = [p["item_id"] for p in product_list[:5]]  # Pegar detalhes dos primeiros 5
    
    product_details = get_product_details(item_ids)
    if not product_details:
        print("❌ Falha ao obter detalhes. Continuando...")
    else:
        print(f"\n📊 Detalhes dos {len(product_details)} produtos:")
        for prod in product_details:
            print(f"\n   Item ID: {prod['item_id']}")
            print(f"   Nome: {prod['item_name']}")
            print(f"   SKU: {prod.get('item_sku', 'N/A')}")
            print(f"   Preço: {prod.get('price', 'N/A')}")
            print(f"   Estoque: {prod.get('stock', 'N/A')}")
            
            if prod.get("has_model"):
                print(f"   Variantes: {len(prod.get('model_list', []))}")
                for model in prod.get("model_list", [])[:2]:
                    print(f"      - {model.get('model_name')} (SKU: {model.get('model_sku')}, Preço: {model.get('price')}, Estoque: {model.get('stock')})")
    
    # ===== PEDIDOS =====
    print("\n\n📋 PASSO 3: LISTAR PEDIDOS (últimos 7 dias)")
    print("-"*70)
    
    end_time = int(time.time())
    start_time = end_time - 7*24*60*60  # 7 dias atrás
    
    orders_list = fetch_all_orders(start_time, end_time, page_size=50)
    if not orders_list:
        print("❌ Falha ao obter pedidos. Pode não haver pedidos nesse período.")
        return

    print(f"\n📊 Pedidos encontrados: {len(orders_list)}")
    
    if not orders_list:
        print("   (Sem pedidos nesse período)")
    else:
        print("   Primeiros pedidos:")
        for idx, order in enumerate(orders_list[:5], 1):
            sn = order.get('order_sn', 'N/A')
            status = order.get('order_status', 'N/A')
            print(f"   {idx}. Order SN: {sn}, Status: {status}")
    
    # ===== DETALHES DE PEDIDOS =====
    print("\n\n💰 PASSO 4: OBTER DETALHES DE PEDIDOS")
    print("-"*70)
    
    if orders_list:
        print("\n💰 PASSO 4: OBTER DETALHES DE TODOS OS PEDIDOS")
        print("-"*70)
        details_collected = []
        for i in range(0, len(orders_list), 50):
            batch_sns = [o["order_sn"] for o in orders_list[i:i+50]]
            detail_batch = get_order_details(batch_sns)
            if detail_batch:
                details_collected.extend(detail_batch)
            time.sleep(0.8)

        if not details_collected:
            print("❌ Falha ao obter detalhes de pedidos.")
        else:
            print(f"\n📊 Detalhes de {len(details_collected)} pedidos:")
            for order in details_collected[:5]:
                print(f"\n   Order SN: {order.get('order_sn', 'N/A')}")
                print(f"   Status: {order.get('order_status', 'N/A')}")
                print(f"   Comprador: {order.get('buyer_username', 'N/A')}")
                print(f"   Total: R$ {order.get('total_amount', 'N/A')}")
                print(f"   Frete: R$ {order.get('actual_shipping_fee', 'N/A')}")
                print(f"   Itens:")
                for item in order.get("item_list", []):
                    qty = item.get("model_quantity_purchased", 1)
                    price = item.get("model_discounted_price", 0)
                    name = item.get('item_name', 'N/A')
                    sku = item.get("model_sku") or item.get("item_sku", "N/A")
                    print(f"      - {name} (SKU: {sku}, Qty: {qty}, Preço unitário: R$ {price})")
                print(f"   Endereço:")
                addr = order.get("recipient_address", {})
                print(f"      {addr.get('name', 'N/A')}, {addr.get('phone', 'N/A')}")
                print(f"      {addr.get('full_address', 'N/A')}")
    else:
        print("   Sem pedidos para buscar detalhes.")
    
    print("\n\n✅ SINCRONIZAÇÃO CONCLUÍDA")
    print("="*70)

if __name__ == "__main__":
    main()
