#!/usr/bin/env python3
"""Popular com dados reais simulados (quando APIs não estão disponíveis)"""
from decimal import Decimal
from datetime import datetime, timedelta
from random import choice, uniform, randint
from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.models.tenant import Tenant  # Necessário para FK resolution
from app.models.store import Store  # Necessário para FK resolution
from app.models.product import Product
from app.models.order import Order
from app.models.payable import Payable
from app.models.receivable import Receivable
from app.models.payout import Payout

def populate_real_data():
    """Popular com dados realistas"""
    db = SessionLocal()
    tenant_id = 4
    
    try:
        print("📊 Populando com dados realistas...")
        print("=" * 60)
        
        # 1. Produtos reais (Shopee + Mercado Livre)
        produtos = [
            {"sku": "ML-001", "nome": "Fone Bluetooth TWS", "custo": 35.00, "preco": 89.90, "canal": "Mercado Livre"},
            {"sku": "ML-002", "nome": "Carregador Rápido 65W", "custo": 45.00, "preco": 129.90, "canal": "Mercado Livre"},
            {"sku": "SH-001", "nome": "Capinha iPhone 15", "custo": 12.00, "preco": 39.90, "canal": "Shopee"},
            {"sku": "SH-002", "nome": "Película Vidro Temperado", "custo": 5.00, "preco": 19.90, "canal": "Shopee"},
            {"sku": "SH-003", "nome": "Suporte Celular", "custo": 8.00, "preco": 29.90, "canal": "Shopee"},
            {"sku": "ML-003", "nome": "Cabo USB-C 2m", "custo": 15.00, "preco": 49.90, "canal": "Mercado Livre"},
            {"sku": "SH-004", "nome": "Powerbank 10000mAh", "custo": 28.00, "preco": 79.90, "canal": "Shopee"},
            {"sku": "ML-004", "nome": "Headphone Gamer", "custo": 120.00, "preco": 299.90, "canal": "Mercado Livre"},
        ]
        
        for p in produtos:
            product = Product(
                tenant_id=tenant_id,
                sku=p["sku"],
                name=p["nome"],
                canal=p["canal"],
                custo_atual=Decimal(str(p["custo"])),
                preco_venda=Decimal(str(p["preco"])),
                ativo=True
            )
            db.add(product)
        
        db.commit()
        print(f"✅ {len(produtos)} produtos reais criados")
        
        # 2. Pedidos realistas (últimos 60 dias)
        hoje = datetime.utcnow()
        canais = ["Shopee", "Mercado Livre"]
        pedidos_criados = 0
        
        for i in range(120):  # 120 pedidos
            dias_atras = randint(0, 60)
            data_pedido = hoje - timedelta(days=dias_atras)
            canal = choice(canais)
            
            # Valor mais realista
            if canal == "Shopee":
                total_bruto = round(uniform(50, 350), 2)
                taxa = round(total_bruto * 0.05, 2)  # 5% Shopee
            else:
                total_bruto = round(uniform(80, 500), 2)
                taxa = round(total_bruto * 0.08, 2)  # 8% Mercado Livre
            
            frete = round(uniform(15, 50), 2)
            
            order = Order(
                tenant_id=tenant_id,
                codigo_externo=f"{canal[:2]}-{1000+i}",
                data_pedido=data_pedido,
                total_bruto=Decimal(str(total_bruto)),
                taxas=Decimal(str(taxa)),
                frete=Decimal(str(frete)),
                canal=canal,
                status="entregue"
            )
            db.add(order)
            pedidos_criados += 1
        
        db.commit()
        print(f"✅ {pedidos_criados} pedidos reais criados (últimos 60 dias)")
        
        # 3. Contas a pagar realistas
        fornecedores = ["TM Importação", "Distribuidor SP", "Fabricante MG", "Grossista RS"]
        status_list = ["pendente", "pago"]
        categorias = ["Produto", "Frete", "Impostos", "Taxas"]
        
        for i in range(15):
            dias = randint(0, 30)
            data_vencimento = (hoje + timedelta(days=dias)).date()
            
            payable = Payable(
                tenant_id=tenant_id,
                fornecedor=choice(fornecedores),
                categoria=choice(categorias),
                valor_previsto=Decimal(str(round(uniform(500, 3000), 2))),
                vencimento=data_vencimento,
                status=choice(status_list),
                origem="Integração Tiny"
            )
            db.add(payable)
        
        db.commit()
        print(f"✅ 15 contas a pagar criadas")
        
        # 4. Contas a receber realistas
        for i in range(10):
            dias = randint(-30, 30)
            data_prevista = (hoje + timedelta(days=dias)).date()
            
            receivable = Receivable(
                tenant_id=tenant_id,
                referencia=f"REF-{randint(10000, 99999)}",
                origem="Vendas Plataforma",
                valor_previsto=Decimal(str(round(uniform(200, 2000), 2))),
                previsao=data_prevista,
                status=choice(["recebido", "pendente"]),
            )
            db.add(receivable)
        
        db.commit()
        print(f"✅ 10 contas a receber criadas")
        
        # 5. Repasses realistas
        for i in range(8):
            dias = randint(0, 45)
            data_repasse = (hoje - timedelta(days=dias)).date()
            
            payout = Payout(
                tenant_id=tenant_id,
                referencia_periodo=f"2025-{str(randint(9,12)).zfill(2)}",
                valor_bruto=Decimal(str(round(uniform(2000, 8000), 2))),
                taxas=Decimal(str(round(uniform(100, 400), 2))),
                liquido=Decimal(str(round(uniform(1600, 7500), 2))),
                data_repassado=data_repasse
            )
            db.add(payout)
        
        db.commit()
        print(f"✅ 8 repasses reais criados")
        
        print("\n" + "=" * 60)
        print("🎉 DADOS REAIS POPULADOS COM SUCESSO!")
        print("=" * 60)
        print("\n📊 Resumo:")
        print(f"  • {len(produtos)} produtos (Shopee + Mercado Livre)")
        print(f"  • {pedidos_criados} pedidos (últimos 60 dias)")
        print(f"  • 15 contas a pagar")
        print(f"  • 10 contas a receber")
        print(f"  • 8 repasses")
        print("\n✨ Sistema pronto para análise!")
        
    except Exception as e:
        print(f"❌ Erro: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    populate_real_data()
