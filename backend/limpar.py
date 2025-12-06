from app.db.session import SessionLocal
from sqlalchemy import text

db = SessionLocal()
tenant_id = 4

try:
    db.execute(text('DELETE FROM payout WHERE tenant_id = :tid'), {'tid': tenant_id})
    db.execute(text('DELETE FROM receivable WHERE tenant_id = :tid'), {'tid': tenant_id})
    db.execute(text('DELETE FROM payable WHERE tenant_id = :tid'), {'tid': tenant_id})
    db.execute(text('DELETE FROM "order" WHERE tenant_id = :tid'), {'tid': tenant_id})
    db.execute(text('DELETE FROM product WHERE tenant_id = :tid'), {'tid': tenant_id})
    db.commit()
    
    prod = db.execute(text('SELECT COUNT(*) FROM product WHERE tenant_id = :tid'), {'tid': tenant_id}).scalar()
    ped = db.execute(text('SELECT COUNT(*) FROM "order" WHERE tenant_id = :tid'), {'tid': tenant_id}).scalar()
    pag = db.execute(text('SELECT COUNT(*) FROM payable WHERE tenant_id = :tid'), {'tid': tenant_id}).scalar()
    rec = db.execute(text('SELECT COUNT(*) FROM receivable WHERE tenant_id = :tid'), {'tid': tenant_id}).scalar()
    rep = db.execute(text('SELECT COUNT(*) FROM payout WHERE tenant_id = :tid'), {'tid': tenant_id}).scalar()
    
    print('🎉 LIMPEZA CONCLUÍDA!')
    print('=' * 50)
    print(f'✅ Produtos: {prod}')
    print(f'✅ Pedidos: {ped}')
    print(f'✅ Contas a Pagar: {pag}')
    print(f'✅ Contas a Receber: {rec}')
    print(f'✅ Repasses: {rep}')
    print('=' * 50)
    print('\nBanco de dados pronto para sincronização real:')
    print('  - Tiny (custo de produtos)')
    print('  - Shopee (pedidos e produtos)')
    print('  - Mercado Livre (pedidos e produtos)')
    
except Exception as e:
    print(f'❌ Erro: {e}')
    db.rollback()
finally:
    db.close()
