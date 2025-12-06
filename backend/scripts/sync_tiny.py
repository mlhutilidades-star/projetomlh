#!/usr/bin/env python3
"""Sincronizar dados reais do Tiny ERP"""
import requests
import os
from decimal import Decimal
from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.models.product import Product

TINY_API_TOKEN = os.getenv("TINY_API_TOKEN", "c3ab46ace723a2421debf7beb13b8b8dbb61453b9650c6919246683f718fc22a")
TINY_BASE_URL = "https://api.tiny.com.br/api/v2"

def sync_tiny_products():
    """Sincronizar produtos do Tiny para AP Gestor"""
    db = SessionLocal()
    tenant_id = 4  # admin@example.com
    
    try:
        print("🔄 Buscando produtos do Tiny ERP...")
        
        # Deletar produtos antigos para atualizar
        db.query(Product).filter(Product.tenant_id == tenant_id).delete()
        db.commit()
        
        # API do Tiny para listar produtos
        url = f"{TINY_BASE_URL}/produtos.json?token={TINY_API_TOKEN}"
        response = requests.get(url, timeout=10)
        
        if response.status_code != 200:
            print(f"❌ Erro na API Tiny: {response.status_code}")
            print(f"   Resposta: {response.text}")
            return
        
        data = response.json()
        
        if "retorno" not in data:
            print("❌ Formato inesperado da API Tiny")
            return
        
        retorno = data.get("retorno", {})
        
        # Verificar se tem produtos
        if "produto" not in retorno:
            print("⚠️  Nenhum produto encontrado no Tiny")
            return
        
        produtos = retorno["produto"]
        
        # Tiny pode retornar um dict (1 produto) ou lista (múltiplos)
        if isinstance(produtos, dict):
            produtos = [produtos]
        
        count = 0
        for prod in produtos:
            try:
                # Extrair dados do produto Tiny
                sku = prod.get("codigo", f"PROD-{prod.get('id', count)}")
                nome = prod.get("nome", "Produto sem nome")
                custo = float(prod.get("preco_custo", 0) or 0)
                preco = float(prod.get("preco", 0) or 0)
                
                # Criar produto no AP Gestor
                product = Product(
                    tenant_id=tenant_id,
                    sku=sku,
                    name=nome,
                    custo_atual=Decimal(str(custo)),
                    preco_venda=Decimal(str(preco)),
                    canal="Tiny",  # Sincronizado do Tiny
                    ativo=True
                )
                db.add(product)
                count += 1
                
                print(f"   ✅ {sku}: {nome} - Custo: R$ {custo:.2f}")
                
            except Exception as e:
                print(f"   ⚠️  Erro ao processar produto: {e}")
                continue
        
        db.commit()
        print(f"\n✅ {count} produtos sincronizados do Tiny ERP!")
        return count
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Erro de conexão: {e}")
        print("   Verifique se o token Tiny está correto e a API está acessível")
        return 0
    except Exception as e:
        print(f"❌ Erro: {e}")
        db.rollback()
        return 0
    finally:
        db.close()

if __name__ == "__main__":
    print("=" * 60)
    print("SINCRONIZAÇÃO TINY ERP → AP GESTOR")
    print("=" * 60)
    sync_tiny_products()
