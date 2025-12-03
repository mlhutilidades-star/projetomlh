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
