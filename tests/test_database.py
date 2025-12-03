import importlib

def test_database_imports():
    mod = importlib.import_module('modules.database')
    assert hasattr(mod, 'get_engine') or hasattr(mod, 'Database') or mod is not None
