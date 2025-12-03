"""
Marca como 'Ignorado' todas as contas importadas do Tiny ERP, conforme solicitação.
Critério: observações contém 'Importado do Tiny ERP'
"""
from modules.database import get_db, ContaPagar

def run():
    db = get_db()
    try:
        rows = db.query(ContaPagar).filter(ContaPagar.observacoes.like('%Importado do Tiny ERP%')).all()
        for row in rows:
            row.status = 'Ignorado'
        db.commit()
        print(f"Marcadas como Ignorado: {len(rows)} contas")
    finally:
        db.close()

if __name__ == '__main__':
    run()
