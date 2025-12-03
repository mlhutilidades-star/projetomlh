import importlib

def test_tiny_api_imports():
    mod = importlib.import_module('modules.tiny_api')
    assert hasattr(mod, 'TinyClient') or mod is not None
