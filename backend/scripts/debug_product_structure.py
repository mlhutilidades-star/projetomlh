#!/usr/bin/env python3
"""
Debug: Ver estrutura completa de um produto
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
    if not path.startswith("/api/v2"):
        path = f"/api/v2{path}"
    base_string = f"{PARTNER_ID}{path}{timestamp}{ACCESS_TOKEN}{SHOP_ID}"
    return hmac.new(PARTNER_KEY.encode(), base_string.encode(), hashlib.sha256).hexdigest()

# Pegar um item_id
path = "/product/get_item_list"
timestamp = int(time.time())
sign = generate_sign(path, timestamp)
resp = requests.get(BASE_URL + path, params={
    "partner_id": PARTNER_ID, "shop_id": SHOP_ID, "timestamp": timestamp,
    "access_token": ACCESS_TOKEN, "sign": sign, "page_size": 1
}).json()

item_id = resp['response']['item'][0]['item_id']
print(f"Testando com item_id: {item_id}\n")

# Obter detalhes completos
path = "/product/get_item_base_info"
timestamp = int(time.time())
sign = generate_sign(path, timestamp)
resp = requests.get(BASE_URL + path, params={
    "partner_id": PARTNER_ID, "shop_id": SHOP_ID, "timestamp": timestamp,
    "access_token": ACCESS_TOKEN, "sign": sign, "item_id_list": str(item_id)
}).json()

product = resp['response']['item_list'][0]

print("="*70)
print("ESTRUTURA COMPLETA DO PRODUTO")
print("="*70)
print(json.dumps(product, indent=2, ensure_ascii=False)[:3000])

print("\n\n" + "="*70)
print("CAMPOS COM VALORES (não-null, não-empty)")
print("="*70)

def print_non_empty(obj, prefix=""):
    if isinstance(obj, dict):
        for k, v in obj.items():
            if v is None or v == "" or v == [] or v == {}:
                continue
            if isinstance(v, (dict, list)) and len(str(v)) > 100:
                print(f"{prefix}{k}: <{type(v).__name__} com {len(v) if isinstance(v, list) else 'fields'}>")
            else:
                print(f"{prefix}{k}: {v}")
    elif isinstance(obj, list):
        for i, item in enumerate(obj[:3]):
            print_non_empty(item, f"{prefix}[{i}].")

print_non_empty(product)

print("\n\n" + "="*70)
print("CAMPOS DE PREÇO E ESTOQUE")
print("="*70)

print(f"price: {product.get('price')}")
print(f"stock: {product.get('stock')}")
print(f"has_model: {product.get('has_model')}")

if product.get("model_list"):
    print(f"model_list: {len(product['model_list'])} models")
    for i, model in enumerate(product['model_list'][:2]):
        print(f"  Model {i}:")
        print(f"    - model_id: {model.get('model_id')}")
        print(f"    - model_name: {model.get('model_name')}")
        print(f"    - model_sku: {model.get('model_sku')}")
        print(f"    - price: {model.get('price')}")
        print(f"    - stock: {model.get('stock')}")
