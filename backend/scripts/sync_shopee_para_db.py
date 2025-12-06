#!/usr/bin/env python3
"""
Sincronização Shopee com Inserção em PostgreSQL
"""
import os
import sys
import requests
import json
import hmac
import hashlib
import time
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Boolean, JSON, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from shopee_token_manager import ensure_access_token, PARTNER_ID, PARTNER_KEY, SHOP_ID, BASE_URL

env_path = Path(__file__).parent.parent.parent / ".env"
load_dotenv(env_path)

# ===== Configuração =====

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/ap_gestor")

# Obter token válido
try:
    ACCESS_TOKEN = ensure_access_token()
except Exception as e:
    print(f"❌ Não foi possível obter access_token: {e}")
    print("➡️  Rode backend/scripts/obter_token_interativo_novo.py para reautorizar.")
    sys.exit(1)

# ===== Modelos SQLAlchemy =====

Base = declarative_base()

class ShopeeProduct(Base):
    __tablename__ = "shopee_products"
    
    id = Column(Integer, primary_key=True)
    tenant_id = Column(Integer, default=4)
    shopee_item_id = Column(Integer, unique=True, index=True)
    name = Column(String(512))
    sku = Column(String(100))
    description = Column(Text, nullable=True)
    category_id = Column(Integer, nullable=True)
    brand = Column(String(255), nullable=True)
    price = Column(Float, nullable=True)
    stock = Column(Integer, nullable=True)
    image_url = Column(String(1024), nullable=True)
    has_model = Column(Boolean, default=False)
    raw_data = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class ShopeeOrder(Base):
    __tablename__ = "shopee_orders"
    
    id = Column(Integer, primary_key=True)
    tenant_id = Column(Integer, default=4)
    order_sn = Column(String(50), unique=True, index=True)
    booking_sn = Column(String(50), nullable=True)
    status = Column(String(50), default="UNKNOWN")
    raw_data = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

# ===== Funções de API =====

def generate_sign(path: str, timestamp: int) -> str:
    if not path.startswith("/api/v2"):
        path = f"/api/v2{path}"
    base_string = f"{PARTNER_ID}{path}{timestamp}{ACCESS_TOKEN}{SHOP_ID}"
    return hmac.new(PARTNER_KEY.encode(), base_string.encode(), hashlib.sha256).hexdigest()

def sync_products_to_db():
    """Sincronizar produtos e inserir em DB"""
    print("\n" + "="*70)
    print("🛍️  SINCRONIZANDO PRODUTOS PARA BANCO DE DADOS")
    print("="*70)
    
    engine = create_engine(DATABASE_URL)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        all_products = []
        offset = 0
        
        # Listar IDs
        print("\n📡 Listando produtos...")
        while True:
            path = "/product/get_item_list"
            timestamp = int(time.time())
            sign = generate_sign(path, timestamp)
            
            params = {
                "partner_id": PARTNER_ID, "shop_id": SHOP_ID, "timestamp": timestamp,
                "access_token": ACCESS_TOKEN, "sign": sign,
                "offset": offset, "page_size": 50, "item_status": "NORMAL"
            }
            
            resp = requests.get(BASE_URL + path, params=params, timeout=10).json()
            if resp.get("error"):
                print(f"   ❌ Erro: {resp['error']}")
                break
            
            all_products.extend(resp["response"]["item"])
            print(f"   ✅ Batch: {len(all_products)} produtos")
            
            if not resp["response"]["has_next_page"]:
                break
            offset = resp["response"].get("next_offset", offset + 50)
            time.sleep(1)
        
        print(f"\n📋 Obtendo detalhes de {len(all_products)} produtos...")
        
        # Obter detalhes
        for i in range(0, len(all_products), 50):
            batch = all_products[i:i+50]
            item_ids = [p["item_id"] for p in batch]
            
            path = "/product/get_item_base_info"
            timestamp = int(time.time())
            sign = generate_sign(path, timestamp)
            
            params = {
                "partner_id": PARTNER_ID, "shop_id": SHOP_ID, "timestamp": timestamp,
                "access_token": ACCESS_TOKEN, "sign": sign,
                "item_id_list": ",".join(str(id) for id in item_ids)
            }
            
            resp = requests.get(BASE_URL + path, params=params, timeout=10).json()
            if resp.get("error"):
                continue
            
            for prod in resp["response"]["item_list"]:
                # Extrair preço/estoque (pode estar em model_list)
                price = prod.get("price")
                stock = prod.get("stock")
                
                if prod.get("has_model") and prod.get("model_list"):
                    first_model = prod["model_list"][0]
                    if not price:
                        price = first_model.get("price")
                    if not stock:
                        stock = first_model.get("stock")
                
                # Extrair imagem
                image_url = None
                if prod.get("image") and prod["image"].get("image_url_list"):
                    image_url = prod["image"]["image_url_list"][0]
                
                # Criar ou atualizar registro
                existing = session.query(ShopeeProduct).filter_by(
                    shopee_item_id=prod["item_id"]
                ).first()
                
                if existing:
                    existing.name = prod.get("item_name")
                    existing.sku = prod.get("item_sku")
                    existing.description = prod.get("description")
                    existing.category_id = prod.get("category_id")
                    existing.brand = prod.get("brand")
                    existing.price = price
                    existing.stock = stock
                    existing.image_url = image_url
                    existing.has_model = prod.get("has_model", False)
                    existing.raw_data = prod
                    existing.updated_at = datetime.utcnow()
                else:
                    product = ShopeeProduct(
                        tenant_id=4,
                        shopee_item_id=prod["item_id"],
                        name=prod.get("item_name"),
                        sku=prod.get("item_sku"),
                        description=prod.get("description"),
                        category_id=prod.get("category_id"),
                        brand=prod.get("brand"),
                        price=price,
                        stock=stock,
                        image_url=image_url,
                        has_model=prod.get("has_model", False),
                        raw_data=prod
                    )
                    session.add(product)
            
            print(f"   ✅ Processado batch {i//50 + 1}")
            time.sleep(1)
        
        session.commit()
        print(f"\n✅ Produtos inseridos/atualizado em DB!")
        
    finally:
        session.close()

def sync_orders_to_db():
    """Sincronizar pedidos e inserir em DB"""
    print("\n" + "="*70)
    print("📋 SINCRONIZANDO PEDIDOS PARA BANCO DE DADOS")
    print("="*70)
    
    engine = create_engine(DATABASE_URL)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        end_time = int(time.time())
        start_time = end_time - 7*24*60*60
        
        all_orders = []
        cursor = None
        
        print(f"\n📡 Listando pedidos...")
        while True:
            path = "/order/get_order_list"
            timestamp = int(time.time())
            sign = generate_sign(path, timestamp)
            
            params = {
                "partner_id": PARTNER_ID, "shop_id": SHOP_ID, "timestamp": timestamp,
                "access_token": ACCESS_TOKEN, "sign": sign,
                "time_range_field": "create_time", "time_from": start_time,
                "time_to": end_time, "page_size": 50
            }
            
            if cursor:
                params["cursor"] = cursor
            
            resp = requests.get(BASE_URL + path, params=params, timeout=10).json()
            if resp.get("error"):
                print(f"   ❌ Erro: {resp['error']}")
                break
            
            all_orders.extend(resp["response"]["order_list"])
            print(f"   ✅ Total: {len(all_orders)} pedidos")
            
            if not resp["response"].get("more"):
                break
            cursor = resp["response"].get("next_cursor")
            time.sleep(1)
        
        # Inserir em DB
        for order in all_orders:
            existing = session.query(ShopeeOrder).filter_by(
                order_sn=order["order_sn"]
            ).first()
            
            if existing:
                existing.booking_sn = order.get("booking_sn")
                existing.raw_data = order
                existing.updated_at = datetime.utcnow()
            else:
                order_record = ShopeeOrder(
                    tenant_id=4,
                    order_sn=order["order_sn"],
                    booking_sn=order.get("booking_sn"),
                    status="UNKNOWN",  # Sem acesso a status na API
                    raw_data=order
                )
                session.add(order_record)
        
        session.commit()
        print(f"\n✅ Pedidos inseridos/atualizados em DB!")
        
    finally:
        session.close()

def main():
    print("="*70)
    print("🚀 SINCRONIZAÇÃO SHOPEE → POSTGRESQL")
    print("="*70)
    
    if not ACCESS_TOKEN:
        print("❌ ACCESS_TOKEN não configurado")
        sys.exit(1)
    
    try:
        sync_products_to_db()
        sync_orders_to_db()
        
        print("\n" + "="*70)
        print("✅ SINCRONIZAÇÃO CONCLUÍDA COM SUCESSO!")
        print("="*70)
        
    except Exception as e:
        print(f"\n❌ ERRO: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
