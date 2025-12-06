#!/usr/bin/env python3
"""Script para limpar dados de teste e deixar apenas dados reais"""
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import os
from datetime import datetime

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+psycopg2://postgres:postgres@db:5432/ap_gestor")

def limpar_dados():
    """Apaga todos os dados de teste, mantendo apenas estrutura"""
    engine = create_engine(DATABASE_URL)
    Session = sessionmaker(bind=engine)
    db = Session()
    
    try:
        # Obter tenant_id para este usuário
        result = db.execute(text("""
            SELECT id FROM tenant WHERE name = 'Tenant Demo' LIMIT 1
        """)).first()
        
        if not result:
            print("❌ Tenant 'Tenant Demo' não encontrado")
            return
        
        tenant_id = result[0]
        print(f"✅ Limpando dados para tenant_id: {tenant_id}")
        
        # Apagar dados mantendo integridade referencial
        deletions = [
            ("payout", "Repasses"),
            ("receivable", "Contas a receber"),
            ("payable", "Contas a pagar"),
            ("order", "Pedidos"),
            ("product", "Produtos"),
        ]
        
        for table, label in deletions:
            db.execute(text(f"DELETE FROM {table} WHERE tenant_id = {tenant_id}"))
            count = db.execute(text(f"SELECT COUNT(*) FROM {table} WHERE tenant_id = {tenant_id}")).scalar()
            print(f"✅ {label} removidos - Restam: {count}")
        
        db.commit()
        print("\n🎉 Todos os dados de teste foram removidos!")
        print("   Banco pronto para sincronização com APIs reais:")
        print("   - Tiny (custo de produtos)")
        print("   - Shopee (pedidos e produtos)")
        
    except Exception as e:
        print(f"❌ Erro ao limpar dados: {str(e)}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    print("🗑️  Limpando dados de teste...")
    print("=" * 60)
    limpar_dados()
