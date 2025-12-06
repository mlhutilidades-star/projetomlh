#!/usr/bin/env python3
"""Sincronizar dados REAIS do Shopee - Anúncios e Pedidos"""
import os
import requests
import json
import hmac
import hashlib
import time
from datetime import datetime, timedelta
from decimal import Decimal
from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.models.tenant import Tenant
from app.models.store import Store
from app.models.product import Product
from app.models.order import Order

# Credenciais Shopee
SHOPEE_PARTNER_ID = os.getenv("SHOPEE_PARTNER_ID", "")
SHOPEE_PARTNER_KEY = os.getenv("SHOPEE_API_PARTNER_KEY", "")  # Para requisições autenticadas
SHOPEE_ACCESS_TOKEN = os.getenv("SHOPEE_ACCESS_TOKEN", "").strip('"')  # Remover aspas se houver
SHOPEE_SHOP_ID = os.getenv("SHOPEE_SHOP_ID", "")

SHOPEE_BASE_URL = "https://partner.shopeemobile.com"
SHOPEE_TIMEOUT = 30

def shopee_sign(path: str, timestamp: int, access_token: str = "", shop_id: str = "") -> str:
    """
    Gerar assinatura HMAC para Shopee API
    
    FÓRMULA CORRETA (descoberta via testes):
    base_string = {partner_id}{path}{timestamp}{access_token}{shop_id}
    sign = HMAC_SHA256(base_string, partner_key)
    """
    # Garantir que não há espaços em branco
    path = str(path).strip()
    timestamp = int(timestamp)
    access_token = str(access_token).strip() if access_token else ""
    shop_id = str(shop_id).strip() if shop_id else ""
    
    if access_token and shop_id:
        # FÓRMULA COMPLETA: partner_id + path + timestamp + access_token + shop_id
        base_string = f"{SHOPEE_PARTNER_ID}{path}{timestamp}{access_token}{shop_id}"
        print(f"  [AUTH] Usando autenticado")
        print(f"  [SIGN] Fórmula: partner_id+path+timestamp+access_token+shop_id")
    else:
        # Requisição sem access_token: partner_id + path + timestamp
        base_string = f"{SHOPEE_PARTNER_ID}{path}{timestamp}"
        print(f"  [AUTH] Usando partner (sem access_token)")
    
    print(f"  [SIGN] Path: '{path}'")
    print(f"  [SIGN] Shop: '{shop_id}'")
    print(f"  [SIGN] Token: '{access_token[:20]}...' (len={len(access_token)})")
    print(f"  [SIGN] Time: {timestamp}")
    print(f"  [SIGN] Base: {base_string[:80]}...")
    
    signature = hmac.new(
        SHOPEE_PARTNER_KEY.encode(),
        base_string.encode(),
        hashlib.sha256
    ).hexdigest()
    
    print(f"  [SIGN] Result: {signature}")
    
    return signature

def sync_shopee_products():
    """Sincronizar anúncios REAIS do Shopee"""
    if not SHOPEE_PARTNER_ID or not SHOPEE_PARTNER_KEY:
        print("❌ Credenciais Shopee não configuradas")
        print("   Configure: SHOPEE_PARTNER_ID, SHOPEE_PARTNER_KEY, SHOPEE_SHOP_ID, SHOPEE_ACCESS_TOKEN")
        return 0
    
    db = SessionLocal()
    tenant_id = 4
    
    print("\n" + "="*70)
    print("🔄 SINCRONIZAÇÃO SHOPEE → ANÚNCIOS")
    print("="*70)
    
    try:
        # Verificar tenant
        tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
        if not tenant:
            print(f"❌ Tenant ID {tenant_id} não encontrado")
            return 0
        
        # Criar store Shopee se não existe
        store = db.query(Store).filter(
            Store.tenant_id == tenant_id,
            Store.name == "Shopee"
        ).first()
        
        if not store:
            store = Store(
                tenant_id=tenant_id,
                name="Shopee",
                tipo="marketplace",
                ativo=True
            )
            db.add(store)
            db.commit()
            print("✅ Loja Shopee criada no sistema")
        
        # Buscar produtos do Shopee
        print(f"\n🔍 Buscando anúncios no Shopee...")
        timestamp = int(time.time())
        path = "/api/v2/product/get_item_list"
        
        # Nota: A chamada exata depende da sua configuração de OAuth
        # Esta é uma chamada simplificada
        
        url = f"{SHOPEE_BASE_URL}{path}"
        
        # Headers para Shopee API v2
        headers = {
            "Content-Type": "application/json",
            "X-API-SOURCE": "postman"
        }
        
        params = {
            "partner_id": SHOPEE_PARTNER_ID,
            "timestamp": timestamp,
            "sign": shopee_sign(path, timestamp, SHOPEE_ACCESS_TOKEN, SHOPEE_SHOP_ID),
            "shop_id": SHOPEE_SHOP_ID,
            "page_size": 100,
            "offset": 0
        }
        
        if SHOPEE_ACCESS_TOKEN:
            params["access_token"] = SHOPEE_ACCESS_TOKEN
        
        response = requests.get(url, params=params, headers=headers, timeout=SHOPEE_TIMEOUT)
        
        if response.status_code != 200:
            print(f"❌ Erro na API Shopee: {response.status_code}")
            print(f"   Response: {response.text[:200]}")
            if response.status_code == 401:
                print("   ⚠️  Token inválido ou expirado")
            elif response.status_code == 429:
                print("   ⚠️  Rate limit atingido")
            return 0
        
        data = response.json()
        
        if data.get("error"):
            print(f"❌ Erro da API: {data.get('error')} - {data.get('error_description', 'Sem descrição')}")
            return 0
        
        items = data.get("response", {}).get("item", [])
        
        if not items:
            print("⚠️  Nenhum anúncio encontrado no Shopee")
            return 0
        
        print(f"\n📦 Encontrados {len(items)} anúncios no Shopee")
        print("-" * 70)
        
        count = 0
        for item in items:
            try:
                # Extrair dados do Shopee
                sku = item.get("sku") or f"SHOP-{item.get('item_id')}"
                nome = item.get("name", "Produto sem nome")
                preco = float(item.get("price_info", {}).get("original_price", 0) or 0)
                estoque = item.get("stock_info", {}).get("current_stock", 0)
                
                if preco <= 0:
                    print(f"   ⚠️  {sku}: Preço zerado, pulando")
                    continue
                
                # Buscar ou criar produto
                product = db.query(Product).filter(
                    Product.tenant_id == tenant_id,
                    Product.sku == sku
                ).first()
                
                if not product:
                    # Produto novo - tentar buscar custo do Tiny
                    # Por enquanto, estimamos 40% de margem
                    custo = preco * 0.6
                    product = Product(
                        tenant_id=tenant_id,
                        sku=sku,
                        name=nome,
                        custo_atual=Decimal(str(custo)),
                        preco_venda=Decimal(str(preco)),
                        canal="Shopee",
                        ativo=True
                    )
                    db.add(product)
                else:
                    # Atualizar preço se mudou
                    product.preco_venda = Decimal(str(preco))
                
                count += 1
                
                print(f"   ✅ {sku}: {nome}")
                print(f"      Preço: R$ {preco:.2f} | Estoque: {estoque} unidades")
                
            except Exception as e:
                print(f"   ⚠️  Erro ao processar: {e}")
                continue
        
        db.commit()
        print("\n" + "-" * 70)
        print(f"✅ {count} anúncios sincronizados do Shopee com sucesso!")
        print("="*70 + "\n")
        
        return count
        
    except requests.exceptions.ConnectionError as e:
        print(f"❌ Erro de conexão: {e}")
        return 0
    except requests.exceptions.Timeout as e:
        print(f"❌ Timeout na requisição: {e}")
        return 0
    except Exception as e:
        print(f"❌ Erro: {e}")
        db.rollback()
        return 0
    finally:
        db.close()

def sync_shopee_orders():
    """Sincronizar pedidos REAIS do Shopee"""
    if not SHOPEE_PARTNER_ID or not SHOPEE_PARTNER_KEY:
        print("❌ Credenciais Shopee não configuradas")
        return 0
    
    db = SessionLocal()
    tenant_id = 4
    
    print("\n" + "="*70)
    print("🔄 SINCRONIZAÇÃO SHOPEE → PEDIDOS")
    print("="*70)
    
    try:
        # Verificar tenant
        tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
        if not tenant:
            print(f"❌ Tenant ID {tenant_id} não encontrado")
            return 0
        
        # Buscar pedidos dos últimos 30 dias
        print(f"\n🔍 Buscando pedidos no Shopee (últimos 30 dias)...")
        
        timestamp = int(time.time())
        path = "/api/v2/order/get_order_list"
        
        url = f"{SHOPEE_BASE_URL}{path}"
        
        headers = {
            "Content-Type": "application/json"
        }
        
        # Data: últimos 15 dias (máximo permitido pela API)
        time_from = int((datetime.now() - timedelta(days=15)).timestamp())
        time_to = int(datetime.now().timestamp())
        
        params = {
            "partner_id": SHOPEE_PARTNER_ID,
            "timestamp": timestamp,
            "sign": shopee_sign(path, timestamp, SHOPEE_ACCESS_TOKEN, SHOPEE_SHOP_ID),
            "shop_id": SHOPEE_SHOP_ID,
            "time_range_field": "create_time",
            "time_from": time_from,
            "time_to": time_to,
            "page_size": 100,
        }
        
        if SHOPEE_ACCESS_TOKEN:
            params["access_token"] = SHOPEE_ACCESS_TOKEN
        
        response = requests.get(url, params=params, headers=headers, timeout=SHOPEE_TIMEOUT)
        
        if response.status_code != 200:
            print(f"❌ Erro na API Shopee: {response.status_code}")
            if response.status_code == 401:
                print("   ⚠️  Token inválido ou expirado")
            return 0
        
        data = response.json()
        
        if data.get("error"):
            print(f"❌ Erro da API: {data.get('error')}")
            return 0
        
        orders_list = data.get("response", {}).get("order_list", [])
        
        if not orders_list:
            print("⚠️  Nenhum pedido encontrado no Shopee")
            return 0
        
        print(f"\n📦 Encontrados {len(orders_list)} pedidos no Shopee")
        print("-" * 70)
        
        count = 0
        for order_data in orders_list:
            try:
                codigo_externo = str(order_data.get("order_sn"))
                valor_total = float(order_data.get("total_amount", 0) or 0)
                data_pedido = datetime.fromtimestamp(order_data.get("create_time", time.time()))
                
                # Verificar se pedido já existe
                existing = db.query(Order).filter(
                    Order.codigo_externo == codigo_externo
                ).first()
                
                if existing:
                    print(f"   ⏭️  {codigo_externo}: Já existe no sistema")
                    continue
                
                # Buscar primeiro produto Shopee para associar
                product = db.query(Product).filter(
                    Product.tenant_id == tenant_id,
                    Product.canal == "Shopee"
                ).first()
                
                if not product:
                    print(f"   ⚠️  {codigo_externo}: Nenhum produto Shopee cadastrado")
                    continue
                
                # Criar pedido
                order = Order(
                    tenant_id=tenant_id,
                    product_id=product.id,
                    codigo_externo=codigo_externo,
                    valor_total=Decimal(str(valor_total)),
                    data_pedido=data_pedido,
                    status="concluído"
                )
                db.add(order)
                count += 1
                
                print(f"   ✅ {codigo_externo}: R$ {valor_total:.2f} em {data_pedido.strftime('%d/%m/%Y')}")
                
            except Exception as e:
                print(f"   ⚠️  Erro ao processar: {e}")
                continue
        
        db.commit()
        print("\n" + "-" * 70)
        print(f"✅ {count} pedidos sincronizados do Shopee com sucesso!")
        print("="*70 + "\n")
        
        return count
        
    except Exception as e:
        print(f"❌ Erro: {e}")
        db.rollback()
        return 0
    finally:
        db.close()

if __name__ == "__main__":
    print("\n🛍️  INTEGRAÇÃO: SHOPEE")
    sync_shopee_products()
    sync_shopee_orders()
