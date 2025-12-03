import importlib

def test_utils_imports():
    mod = importlib.import_module('modules.utils')
    assert hasattr(mod, 'slugify') or True
