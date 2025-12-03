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

# --- Force writable SQLite DB for CI/tests at module level ---
# This MUST run before any test module imports database.py
# Set a default DATABASE_URL to a file if not already set to an absolute path
existing_url = os.environ.get('DATABASE_URL', '').strip()
if not existing_url or existing_url == 'sqlite:///:memory:' or (existing_url.startswith('sqlite:///') and not existing_url.startswith('sqlite:////')):
    # Not set or is memory or is relative path - force it to absolute
    if existing_url.startswith('sqlite:////'):
        # Already an absolute path, keep it
        pass
    else:
        # Force to data/mlh_test.db
        TEST_DB_URL = "sqlite:///./data/mlh_test.db"
        os.environ['DATABASE_URL'] = TEST_DB_URL

# Proactively create the data directory to avoid readonly path issues
try:
    Path(ROOT / "data").mkdir(parents=True, exist_ok=True)
except Exception as e:
    print(f"[tests] Warning: could not create data dir: {e}")

@pytest.fixture(scope='session', autouse=True)
def ensure_writable_sqlite(tmp_path_factory):
    """
    Garante que os testes usem um arquivo sqlite gravável quando necessário
    e tenta criar o schema via SQLAlchemy em modo best-effort.
    """
    db_url = os.environ.get('DATABASE_URL', '').strip()
    needs_reinit = False
    
    if db_url == 'sqlite:///:memory:' or db_url == '' or (db_url.startswith('sqlite:///') and not db_url.startswith('sqlite:////')):
        dbdir = tmp_path_factory.mktemp('db')
        dbfile = dbdir / 'test_db.sqlite'
        dbfile.write_text('')
        dbfile.chmod(0o666)
        os.environ['DATABASE_URL'] = f"sqlite:///{dbfile}"
        needs_reinit = True
    else:
        # Se for caminho absoluto sqlite:////...
        if db_url.startswith('sqlite:////'):
            path_str = db_url.replace('sqlite:///', '/')
            p = Path(path_str)
            p.parent.mkdir(parents=True, exist_ok=True)
            if not p.exists():
                p.touch()
            p.chmod(0o666)

    # Se mudamos a URL, precisamos reinicializar o engine do database module
    if needs_reinit:
        try:
            from sqlalchemy import create_engine
            from sqlalchemy.orm import sessionmaker
            import modules.database as db_module
            # Recriar engine com novo URL
            db_module.DATABASE_URL = os.environ['DATABASE_URL']
            db_module.engine = create_engine(db_module.DATABASE_URL, echo=False)
            db_module.SessionLocal = sessionmaker(bind=db_module.engine)
        except Exception:
            pass

    # Best-effort: tentar criar schema via SQLAlchemy se disponível.
    try:
        from sqlalchemy import create_engine
        try:
            # Criar schema para modules.database.Base
            from modules.database import Base as ModulesBase
            engine = create_engine(os.environ['DATABASE_URL'])
            ModulesBase.metadata.create_all(engine)
        except Exception:
            pass
        
        try:
            # Criar schema para models.contas_pagar.Base
            from models.contas_pagar import Base as ModelsBase
            engine = create_engine(os.environ['DATABASE_URL'])
            ModelsBase.metadata.create_all(engine)
        except Exception:
            pass
    except Exception:
        pass
    
    yield

# Initialize database before any tests run to ensure tables exist
# This fixture depends on ensure_writable_sqlite to run first
@pytest.fixture(scope="session", autouse=True)
def _init_db_session(ensure_writable_sqlite):
    from modules.database import init_database
    init_database()
    yield
