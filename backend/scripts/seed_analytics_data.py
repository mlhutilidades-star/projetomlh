"""
Script para popular dados de exemplo para analytics
Rode com: python scripts/seed_analytics_data.py
"""
import sys
import os
from datetime import datetime, timedelta
from decimal import Decimal
from random import randint, choice, uniform

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.db.session import SessionLocal
from app.models.tenant import Tenant
from app.models.store import Store
from app.models.order import Order
from app.models.product import Product
from app.models.payable import Payable
from app.models.receivable import Receivable
from app.models.payout import Payout
from sqlalchemy import text


def seed_analytics_data():
    db = SessionLocal()
    
    try:
        # Pega tenant_id do admin (assumindo que é 4 baseado nos logs anteriores)
        result = db.execute(text("SELECT tenant_id FROM \"user\" WHERE email = 'admin@example.com' LIMIT 1"))
        row = result.fetchone()
        if not row:
            print("❌ Admin user não encontrado")
            return
        
        tenant_id = row[0]
        print(f"✅ Usando tenant_id: {tenant_id}")
        
        # Limpar dados anteriores de analytics (opcional)
        db.query(Order).filter(Order.tenant_id == tenant_id).delete()
        db.query(Product).filter(Product.tenant_id == tenant_id).delete()
        db.query(Payable).filter(Payable.tenant_id == tenant_id).delete()
        db.query(Receivable).filter(Receivable.tenant_id == tenant_id).delete()
        db.query(Payout).filter(Payout.tenant_id == tenant_id).delete()
        db.commit()
        print("✅ Dados anteriores limpos")
        
        # Criar produtos de exemplo
        produtos = [
            {"sku": "PROD-001", "nome": "Camiseta Básica", "custo": 25.00, "preco": 49.90, "canal": "Shopee"},
            {"sku": "PROD-002", "nome": "Calça Jeans", "custo": 80.00, "preco": 159.90, "canal": "Shopee"},
            {"sku": "PROD-003", "nome": "Tênis Esportivo", "custo": 120.00, "preco": 249.90, "canal": "Mercado Livre"},
            {"sku": "PROD-004", "nome": "Boné Trucker", "custo": 15.00, "preco": 39.90, "canal": "Shopee"},
            {"sku": "PROD-005", "nome": "Jaqueta Jeans", "custo": 100.00, "preco": 199.90, "canal": "Mercado Livre"},
        ]
        
        for p in produtos:
            product = Product(
                tenant_id=tenant_id,
                sku=p["sku"],
                nome=p["nome"],
                canal=p["canal"],
                custo_atual=Decimal(str(p["custo"])),
                preco_venda=Decimal(str(p["preco"])),
                ativo=True
            )
            db.add(product)
        
        db.commit()
        print(f"✅ {len(produtos)} produtos criados")
        
        # Criar pedidos dos últimos 90 dias (apenas de plataformas de venda: Shopee e Mercado Livre)
        canais = ["Shopee", "Mercado Livre"]
        hoje = datetime.utcnow()
        
        for i in range(100):
            dias_atras = randint(0, 90)
            data_pedido = hoje - timedelta(days=dias_atras)
            canal = choice(canais)
            
            total_bruto = Decimal(str(round(uniform(50, 500), 2)))
            taxas = total_bruto * Decimal("0.15")  # 15% de taxa
            frete = Decimal(str(round(uniform(10, 30), 2)))
            liquido = total_bruto - taxas - frete
            
            order = Order(
                tenant_id=tenant_id,
                codigo_externo=f"PED-{1000+i}",
                canal=canal,
                status="entregue",
                total_bruto=total_bruto,
                taxas=taxas,
                frete=frete,
                liquido=liquido,
                data_pedido=data_pedido
            )
            db.add(order)
        
        db.commit()
        print("✅ 100 pedidos criados")
        
        # Criar contas a pagar
        categorias = ["Fornecedor", "Despesa Operacional", "Marketing", "Logística"]
        for i in range(20):
            dias_venc = randint(-30, 60)
            vencimento = (hoje + timedelta(days=dias_venc)).date()
            status = "pendente" if dias_venc > 0 else choice(["pago", "pendente"])
            
            payable = Payable(
                tenant_id=tenant_id,
                fornecedor=f"Fornecedor {i+1}",
                categoria=choice(categorias),
                vencimento=vencimento,
                valor_previsto=Decimal(str(round(uniform(100, 5000), 2))),
                status=status,
                origem="manual"
            )
            db.add(payable)
        
        db.commit()
        print("✅ 20 contas a pagar criadas")
        
        # Criar contas a receber
        for i in range(15):
            dias_prev = randint(-15, 45)
            previsao = (hoje + timedelta(days=dias_prev)).date()
            status = "pendente" if dias_prev > 0 else "recebido"
            
            receivable = Receivable(
                tenant_id=tenant_id,
                origem=choice(canais),
                referencia=f"REC-{2000+i}",
                previsao=previsao,
                valor_previsto=Decimal(str(round(uniform(200, 3000), 2))),
                status=status
            )
            db.add(receivable)
        
        db.commit()
        print("✅ 15 contas a receber criadas")
        
        # Criar repasses
        for i in range(10):
            dias_atras = randint(0, 30)
            created_at = hoje - timedelta(days=dias_atras)
            
            payout = Payout(
                tenant_id=tenant_id,
                referencia_periodo=f"2024-{10+i%3}",
                valor_bruto=Decimal(str(round(uniform(500, 5000), 2))),
                taxas=Decimal(str(round(uniform(50, 500), 2))),
                liquido=Decimal(str(round(uniform(450, 4500), 2))),
                data_repassado=created_at.date()
            )
            db.add(payout)
        
        db.commit()
        print("✅ 10 repasses criados")
        
        print("\n🎉 Seed de dados de analytics concluído com sucesso!")
        print(f"   Tenant ID: {tenant_id}")
        print("   Agora você pode acessar as páginas de analytics com dados reais.")
        
    except Exception as e:
        print(f"❌ Erro ao criar dados: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_analytics_data()
