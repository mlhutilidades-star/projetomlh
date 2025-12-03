import os
import sys
from pathlib import Path
import pytest
import logging

# Ensure project root is on sys.path
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# Import shared fixtures
pytest_plugins = ['tests.fixtures']

# Set up logging for test configuration
logger = logging.getLogger('tests.conftest')

def is_memory_or_relative_url(url: str) -> bool:
    """Check if DATABASE_URL is memory or relative path (needs fixing)."""
    if not url or url == 'sqlite:///:memory:':
        return True
    if url.startswith('sqlite:///') and not url.startswith('sqlite:////'):
        return True
    return False

def ensure_db_file_writable(db_path: Path) -> None:
    """Ensure database file exists and is writable."""
    db_path.parent.mkdir(parents=True, exist_ok=True)
    if not db_path.exists():
        db_path.touch()
    db_path.chmod(0o666)

# --- Force writable SQLite DB for CI/tests at module level ---
# This MUST run before any test module imports database.py
existing_url = os.environ.get('DATABASE_URL', '').strip()
if is_memory_or_relative_url(existing_url):
    if not existing_url.startswith('sqlite:////'):
        # Force to data/mlh_test.db
        TEST_DB_URL = "sqlite:///./data/mlh_test.db"
        os.environ['DATABASE_URL'] = TEST_DB_URL

# Proactively create the data directory to avoid readonly path issues
try:
    Path(ROOT / "data").mkdir(parents=True, exist_ok=True)
except Exception as e:
    logger.warning(f"Could not create data dir: {e}")

@pytest.fixture(scope='session', autouse=True)
def ensure_writable_sqlite(tmp_path_factory):
    """
    Garante que os testes usem um arquivo sqlite gravável quando necessário
    e tenta criar o schema via SQLAlchemy em modo best-effort.
    """
    db_url = os.environ.get('DATABASE_URL', '').strip()
    needs_reinit = False
    
    if is_memory_or_relative_url(db_url):
        # Use temp directory for memory/relative URLs
        dbdir = tmp_path_factory.mktemp('db')
        dbfile = dbdir / 'test_db.sqlite'
        dbfile.write_text('')
        dbfile.chmod(0o666)
        os.environ['DATABASE_URL'] = f"sqlite:///{dbfile}"
        needs_reinit = True
    elif db_url.startswith('sqlite:////'):
        # Absolute path - ensure it's writable
        path_str = db_url.replace('sqlite:///', '/')
        p = Path(path_str)
        ensure_db_file_writable(p)

    # Reinitialize database engine if URL changed
    if needs_reinit:
        try:
            from sqlalchemy import create_engine
            from sqlalchemy.orm import sessionmaker
            import modules.database as db_module
            db_module.DATABASE_URL = os.environ['DATABASE_URL']
            db_module.engine = create_engine(db_module.DATABASE_URL, echo=False)
            db_module.SessionLocal = sessionmaker(bind=db_module.engine)
        except ImportError as e:
            logger.error(f"Failed to import database module: {e}")
        except Exception as e:
            logger.error(f"Failed to reinitialize engine: {e}")

    # Create schemas for both database models (best-effort)
    _create_database_schemas()
    
    yield

def _create_database_schemas():
    """Create database schemas from both Base models (best-effort)."""
    from sqlalchemy import create_engine
    
    # Try modules.database.Base
    try:
        from modules.database import Base as ModulesBase
        engine = create_engine(os.environ['DATABASE_URL'])
        ModulesBase.metadata.create_all(engine)
    except ImportError:
        logger.debug("modules.database not available")
    except Exception as e:
        logger.warning(f"Failed to create modules.database schema: {e}")
    
    # Try models.contas_pagar.Base
    try:
        from models.contas_pagar import Base as ModelsBase
        engine = create_engine(os.environ['DATABASE_URL'])
        ModelsBase.metadata.create_all(engine)
    except ImportError:
        logger.debug("models.contas_pagar not available")
    except Exception as e:
        logger.warning(f"Failed to create models.contas_pagar schema: {e}")

# Initialize database before any tests run to ensure tables exist
# This fixture depends on ensure_writable_sqlite to run first
@pytest.fixture(scope="session", autouse=True)
def _init_db_session(ensure_writable_sqlite):
    from modules.database import init_database
    init_database()
    yield
