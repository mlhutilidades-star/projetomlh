import os
import sys
from pathlib import Path
import pytest

# Ensure project root is on sys.path
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# Set TESTING environment variable for cache module
os.environ['TESTING'] = '1'

# Import shared fixtures
pytest_plugins = ['tests.fixtures']

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
