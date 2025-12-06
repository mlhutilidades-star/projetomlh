#!/usr/bin/env python3
"""Sincronizar dados REAIS do Tiny ERP - Produtos e Custos"""
import os
import requests
from decimal import Decimal
from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.models.tenant import Tenant
from app.models.store import Store
from app.models.product import Product

TINY_API_TOKEN = os.getenv("TINY_API_TOKEN", "c3ab46ace723a2421debf7beb13b8b8dbb61453b9650c6919246683f718fc22a")
TINY_BASE_URL = "https://api.tiny.com.br/api/v2"
TINY_TIMEOUT = 30

def sync_tiny_products():
    """Sincronizar produtos reais do Tiny ERP"""
    db = SessionLocal()
    tenant_id = 4  # admin@example.com
    
    print("\n" + "="*70)
    print("🔄 SINCRONIZAÇÃO TINY ERP → PRODUTOS")
    print("="*70)
    
    try:
        # Verificar se tenant existe
        tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
        if not tenant:
            print(f"❌ Tenant ID {tenant_id} não encontrado")
            return 0
        
        # Deletar produtos anteriores para atualizar
        db.query(Product).filter(Product.tenant_id == tenant_id).delete()
        db.commit()
        print("✅ Produtos antigos removidos")
        
        # Buscar produtos do Tiny
        print(f"\n🔍 Buscando produtos no Tiny...")
        url = f"{TINY_BASE_URL}/produtos.json"
        params = {"token": TINY_API_TOKEN}
        
        response = requests.get(url, params=params, timeout=TINY_TIMEOUT)
        
        if response.status_code != 200:
            print(f"❌ Erro na API Tiny: {response.status_code}")
            if response.status_code == 403:
                print("   Token inválido ou expirado")
            elif response.status_code == 429:
                print("   Rate limit atingido")
            return 0
        
        data = response.json()
        
        if "retorno" not in data or "erro" in data.get("retorno", {}):
            erro = data.get("retorno", {}).get("erro", "Erro desconhecido")
            print(f"❌ Erro da API: {erro}")
            return 0
        
        retorno = data.get("retorno", {})
        
        # Verificar se tem produtos
        if "produto" not in retorno:
            print("⚠️  Nenhum produto encontrado no Tiny")
            return 0
        
        produtos = retorno["produto"]
        
        # Tiny pode retornar um dict (1 produto) ou lista (múltiplos)
        if isinstance(produtos, dict):
            produtos = [produtos]
        
        print(f"\n📦 Encontrados {len(produtos)} produtos no Tiny")
        print("-" * 70)
        
        count = 0
        for prod in produtos:
            try:
                # Extrair dados do produto Tiny
                sku = prod.get("codigo", f"PROD-{prod.get('id', count)}")
                nome = prod.get("nome", "Produto sem nome")
                custo = float(prod.get("preco_custo", 0) or 0)
                preco = float(prod.get("preco", 0) or 0)
                ativo = prod.get("ativo") == "S"
                
                if custo <= 0:
                    print(f"   ⚠️  {sku}: Custo zerado, pulando")
                    continue
                
                # Criar produto no AP Gestor
                product = Product(
                    tenant_id=tenant_id,
                    sku=sku,
                    name=nome,
                    custo_atual=Decimal(str(custo)),
                    preco_venda=Decimal(str(preco)),
                    canal="Tiny",  # Origem: Tiny ERP
                    ativo=ativo
                )
                db.add(product)
                count += 1
                
                margem = ((preco - custo) / custo * 100) if custo > 0 else 0
                print(f"   ✅ {sku}: {nome}")
                print(f"      Custo: R$ {custo:.2f} | Venda: R$ {preco:.2f} | Margem: {margem:.1f}%")
                
            except Exception as e:
                print(f"   ⚠️  Erro ao processar: {e}")
                continue
        
        db.commit()
        print("\n" + "-" * 70)
        print(f"✅ {count} produtos sincronizados do Tiny ERP com sucesso!")
        print("="*70 + "\n")
        
        return count
        
    except requests.exceptions.ConnectionError as e:
        print(f"❌ Erro de conexão: {e}")
        print("   Verifique sua conexão com a internet")
        return 0
    except requests.exceptions.Timeout as e:
        print(f"❌ Timeout na requisição: {e}")
        print(f"   API Tiny não respondeu em {TINY_TIMEOUT}s")
        return 0
    except Exception as e:
        print(f"❌ Erro: {e}")
        db.rollback()
        return 0
    finally:
        db.close()

if __name__ == "__main__":
    print("\n🔗 INTEGRAÇÃO: TINY ERP")
    sync_tiny_products()
