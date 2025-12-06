#!/usr/bin/env python3
"""Limpar dados simulados - Deixar apenas estrutura para dados REAIS"""
from sqlalchemy import text
from app.db.session import SessionLocal

def limpar_dados_simulados():
    """Deletar todos os dados simulados mantendo estrutura"""
    db = SessionLocal()
    
    print("\n" + "="*70)
    print("🗑️  LIMPEZA DE DADOS SIMULADOS")
    print("="*70)
    print("\nVou deletar TODOS os dados de teste/simulados:")
    print("  - Produtos")
    print("  - Pedidos")
    print("  - Contas a Pagar")
    print("  - Contas a Receber")
    print("  - Repasses")
    print("\nMantendo:")
    print("  ✅ Estrutura de banco (tabelas)")
    print("  ✅ Lojas")
    print("  ✅ Tenants")
    
    try:
        tenant_id = 4  # admin@example.com
        
        # Deletar em ordem de dependência
        print("\n" + "-" * 70)
        
        # Payouts (depende de Order)
        result = db.execute(
            text("DELETE FROM payout WHERE id IN (SELECT p.id FROM payout p WHERE EXISTS (SELECT 1 FROM \"order\" o WHERE o.id = p.order_id AND o.tenant_id = :tid))"),
            {"tid": tenant_id}
        )
        print(f"✅ {result.rowcount} repasses deletados")
        
        # Receivables
        result = db.execute(
            text("DELETE FROM receivable WHERE tenant_id = :tid"),
            {"tid": tenant_id}
        )
        print(f"✅ {result.rowcount} contas a receber deletadas")
        
        # Payables
        result = db.execute(
            text("DELETE FROM payable WHERE tenant_id = :tid"),
            {"tid": tenant_id}
        )
        print(f"✅ {result.rowcount} contas a pagar deletadas")
        
        # Orders
        result = db.execute(
            text("DELETE FROM \"order\" WHERE tenant_id = :tid"),
            {"tid": tenant_id}
        )
        print(f"✅ {result.rowcount} pedidos deletados")
        
        # Products
        result = db.execute(
            text("DELETE FROM product WHERE tenant_id = :tid"),
            {"tid": tenant_id}
        )
        print(f"✅ {result.rowcount} produtos deletados")
        
        db.commit()
        
        print("\n" + "-" * 70)
        print("✅ BANCO DE DADOS LIMPO COM SUCESSO!")
        print("\n📝 Próximos passos:")
        print("   1. Configure o token Tiny em backend/.env")
        print("   2. Execute: python scripts/sync_tiny_real.py")
        print("   3. Configure credenciais Shopee em backend/.env")
        print("   4. Execute: python scripts/sync_shopee_real.py")
        print("   5. Veja os dados REAIS em http://localhost:3000/dashboard")
        print("\n💡 Para mais info, leia: INTEGRACAO_REAL.md")
        print("="*70 + "\n")
        
    except Exception as e:
        print(f"\n❌ Erro: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    limpar_dados_simulados()
