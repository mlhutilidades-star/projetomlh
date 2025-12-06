#!/usr/bin/env python3
"""
Teste para ver respostas brutas da API
"""
import os
import sys
import requests
import json
import hmac
import hashlib
import time
from pathlib import Path
from dotenv import load_dotenv

env_path = Path(__file__).parent.parent.parent / ".env"
load_dotenv(env_path)

PARTNER_ID = int(os.getenv("SHOPEE_PARTNER_ID", "2013808"))
PARTNER_KEY = os.getenv("SHOPEE_API_PARTNER_KEY", "")
ACCESS_TOKEN = os.getenv("SHOPEE_ACCESS_TOKEN", "").strip('"').strip()
SHOP_ID = int(os.getenv("SHOPEE_SHOP_ID", "1616902621"))

BASE_URL = "https://partner.shopeemobile.com/api/v2"

def generate_sign(path: str, timestamp: int) -> str:
    """Gera assinatura HMAC-SHA256"""
    if not path.startswith("/api/v2"):
        path = f"/api/v2{path}"
    
    base_string = f"{PARTNER_ID}{path}{timestamp}{ACCESS_TOKEN}{SHOP_ID}"
    signature = hmac.new(
        PARTNER_KEY.encode(),
        base_string.encode(),
        hashlib.sha256
    ).hexdigest()
    return signature

def test_product_list():
    path = "/product/get_item_list"
    timestamp = int(time.time())
    sign = generate_sign(path, timestamp)
    
    params = {
        "partner_id": PARTNER_ID,
        "shop_id": SHOP_ID,
        "timestamp": timestamp,
        "access_token": ACCESS_TOKEN,
        "sign": sign,
        "offset": 0,
        "page_size": 2,
        "item_status": "NORMAL"
    }
    
    url = BASE_URL + path
    print("\n" + "="*70)
    print("TESTE 1: LISTAGEM DE PRODUTOS")
    print("="*70)
    print(f"URL: {url}")
    print(f"Base string para signature: {PARTNER_ID}/api/v2{path}{timestamp}{ACCESS_TOKEN}{SHOP_ID}")
    
    resp = requests.get(url, params=params)
    data = resp.json()
    
    print(f"\nStatus: {resp.status_code}")
    print(f"\nResposta JSON (completo):")
    print(json.dumps(data, indent=2, ensure_ascii=False))

def test_product_details():
    """Testar get_item_base_info com um produto da lista"""
    # Primeiro pegar um item_id
    path = "/product/get_item_list"
    timestamp = int(time.time())
    sign = generate_sign(path, timestamp)
    
    params = {
        "partner_id": PARTNER_ID,
        "shop_id": SHOP_ID,
        "timestamp": timestamp,
        "access_token": ACCESS_TOKEN,
        "sign": sign,
        "offset": 0,
        "page_size": 1,
        "item_status": "NORMAL"
    }
    
    url = BASE_URL + path
    resp = requests.get(url, params=params).json()
    
    if not resp['response']['item']:
        print("Nenhum produto encontrado")
        return
    
    item_id = resp['response']['item'][0]['item_id']
    
    # Agora testar get_item_base_info
    path = "/product/get_item_base_info"
    timestamp = int(time.time())
    sign = generate_sign(path, timestamp)
    
    params = {
        "partner_id": PARTNER_ID,
        "shop_id": SHOP_ID,
        "timestamp": timestamp,
        "access_token": ACCESS_TOKEN,
        "sign": sign,
        "item_id_list": str(item_id),
        "need_tax_info": "false",
        "need_complaint_policy": "false"
    }
    
    url = BASE_URL + path
    print("\n" + "="*70)
    print(f"TESTE 2: DETALHES DO PRODUTO {item_id}")
    print("="*70)
    print(f"URL: {url}")
    
    resp = requests.get(url, params=params)
    data = resp.json()
    
    print(f"\nStatus: {resp.status_code}")
    print(f"\nResposta JSON (completo):")
    print(json.dumps(data, indent=2, ensure_ascii=False)[:2000])

def test_order_list():
    end_time = int(time.time())
    start_time = end_time - 7*24*60*60
    
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
        "page_size": 2
    }
    
    url = BASE_URL + path
    print("\n" + "="*70)
    print("TESTE 3: LISTAGEM DE PEDIDOS")
    print("="*70)
    print(f"URL: {url}")
    
    resp = requests.get(url, params=params)
    data = resp.json()
    
    print(f"\nStatus: {resp.status_code}")
    print(f"\nResposta JSON (completo):")
    print(json.dumps(data, indent=2, ensure_ascii=False)[:2000])
    
    # Se houver pedidos, testar order details
    if data['response']['order_list']:
        test_order_details(data['response']['order_list'][:1])

def test_order_details(orders):
    order_sn = orders[0]['order_sn']
    
    path = "/order/get_order_detail"
    timestamp = int(time.time())
    sign = generate_sign(path, timestamp)
    
    params = {
        "partner_id": PARTNER_ID,
        "shop_id": SHOP_ID,
        "timestamp": timestamp,
        "access_token": ACCESS_TOKEN,
        "sign": sign,
        "order_sn_list": json.dumps([order_sn]),
        "response_optional_fields": "order_status,buyer_username,item_list,total_amount"
    }
    
    url = BASE_URL + path
    print("\n" + "="*70)
    print(f"TESTE 4: DETALHES DO PEDIDO {order_sn}")
    print("="*70)
    print(f"URL: {url}")
    print(f"order_sn_list: {json.dumps([order_sn])}")
    
    resp = requests.get(url, params=params)
    data = resp.json()
    
    print(f"\nStatus: {resp.status_code}")
    print(f"\nResposta JSON (completo):")
    print(json.dumps(data, indent=2, ensure_ascii=False)[:2000])

if __name__ == "__main__":
    test_product_list()
    test_product_details()
    test_order_list()
