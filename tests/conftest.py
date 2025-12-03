import os
import sys
from pathlib import Path
import pytest

# Ensure project root is on sys.path
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# Import shared fixtures
pytest_plugins = ['tests.fixtures']

@pytest.fixture(scope='session', autouse=True)
def ensure_writable_sqlite(tmp_path_factory):
    """
    Garante que os testes usem um arquivo sqlite gravável quando necessário
    e tenta criar o schema via SQLAlchemy em modo best-effort.
    """
    db_url = os.environ.get('DATABASE_URL', '').strip()
    if db_url == 'sqlite:///:memory:' or db_url == '' or (db_url.startswith('sqlite:///') and not db_url.startswith('sqlite:////')):
        dbdir = tmp_path_factory.mktemp('db')
        dbfile = dbdir / 'test_db.sqlite'
        dbfile.write_text('')
        dbfile.chmod(0o666)
        os.environ['DATABASE_URL'] = f"sqlite:///{dbfile}"
    else:
        # Se for caminho absoluto sqlite:////...
        if db_url.startswith('sqlite:////'):
            path_str = db_url.replace('sqlite:///', '/')
            p = Path(path_str)
            p.parent.mkdir(parents=True, exist_ok=True)
            if not p.exists():
                p.touch()
            p.chmod(0o666)

    # Best-effort: tentar criar schema via SQLAlchemy se disponível.
    try:
        from sqlalchemy import create_engine
        try:
            # Ajuste o import abaixo para o módulo real que define Base/metadata do projeto
            # Exemplo: from projetomlh.models import Base
            from modules.database import Base  # <-- SUBSTITUIR 'app.models' pelo módulo real do projeto
            engine = create_engine(os.environ['DATABASE_URL'])
            Base.metadata.create_all(engine)
        except Exception:
            # se import falhar, continuar; migrações devem ser aplicadas explicitamente no CI
            pass
    except Exception:
        pass

# --- Ensure a writable SQLite DB for CI/tests ---
# Set a default DATABASE_URL to a file under ./data if not provided.
TEST_DB_URL = "sqlite:///./data/mlh_test.db"
os.environ.setdefault("DATABASE_URL", TEST_DB_URL)

# Proactively create the data directory to avoid readonly path issues
try:
    Path(ROOT / "data").mkdir(parents=True, exist_ok=True)
except Exception as e:
    print(f"[tests] Warning: could not create data dir: {e}")

# Initialize database before any tests run to ensure tables exist
@pytest.fixture(scope="session", autouse=True)
def _init_db_session():
    from modules.database import init_database
    init_database()
    yield
