#!/usr/bin/env python3
"""
Teste mais simples: apenas verificar se Partner está ativo
"""
import requests
import json

SHOPEE_API = "https://partner.shopeemobile.com/api/v2"

print("\n" + "="*80)
print("🔍 TESTE SIMPLES: Health Check da API Shopee")
print("="*80)

# Teste 1: ping public (sem autenticação)
print("\n\n1️⃣  Teste: /public/ping (sem autenticação)")
print("-" * 80)
try:
    response = requests.get(f"{SHOPEE_API}/public/ping", timeout=5)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text[:200]}")
except Exception as e:
    print(f"Erro: {e}")

# Teste 2: Partner authentication test endpoint
print("\n\n2️⃣  Teste: Verificar Partner ativo")
print("-" * 80)

PARTNER_ID = "2013808"
SHOP_ID = "1616902621"
ACCESS_TOKEN = "54666a41686a75534a61527167454353"

try:
    # Teste 1: GET shop info SEM nada
    response = requests.get(
        f"{SHOPEE_API}/shop/get_shop_info",
        timeout=5
    )
    print(f"Sem params: {response.status_code} - {response.json().get('message', '')[:100]}")
    
    # Teste 2: Com shop_id apenas
    response = requests.get(
        f"{SHOPEE_API}/shop/get_shop_info",
        params={"shop_id": SHOP_ID},
        timeout=5
    )
    print(f"Com shop_id: {response.status_code} - {response.json().get('message', '')[:100]}")
    
    # Teste 3: Com partner_id
    response = requests.get(
        f"{SHOPEE_API}/shop/get_shop_info",
        params={"partner_id": PARTNER_ID},
        timeout=5
    )
    print(f"Com partner_id: {response.status_code} - {response.json().get('message', '')[:100]}")
    
    # Teste 4: Com access_token como header
    response = requests.get(
        f"{SHOPEE_API}/shop/get_shop_info",
        params={"shop_id": SHOP_ID},
        headers={"X-Shopee-Access-Token": ACCESS_TOKEN},
        timeout=5
    )
    print(f"Com header token: {response.status_code} - {response.text[:100]}")
    
except Exception as e:
    print(f"Erro: {e}")

# Teste 3: Lista de endpoints possíveis
print("\n\n3️⃣  Teste: Listar endpoints funcionais")
print("-" * 80)

endpoints = [
    "/product/get_item_list",
    "/product/get_item_base_info",
    "/product/search_item_by_sku",
    "/merchant/get_merchant_info",
    "/account/account_info",
]

for endpoint in endpoints:
    try:
        response = requests.head(f"{SHOPEE_API}{endpoint}", timeout=3)
        status = response.status_code
        print(f"{endpoint}: {status}")
    except:
        print(f"{endpoint}: Erro de conexão")

print("\n" + "="*80)
