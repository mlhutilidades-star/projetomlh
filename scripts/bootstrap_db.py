import os
import sys
from pathlib import Path

# Add project root to path
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

def main():
    try:
        from sqlalchemy import create_engine
        # Ajuste o import abaixo para apontar ao Base/metadata do seu projeto:
        from modules.database import Base  # <-- SUBSTITUIR para o caminho correto
        engine = create_engine(os.environ['DATABASE_URL'])
        Base.metadata.create_all(engine)
        print('Schema created successfully.')
    except Exception as e:
        print('bootstrap_db: failed (adapt imports or use migrations):', e)

if __name__ == '__main__':
    main()
