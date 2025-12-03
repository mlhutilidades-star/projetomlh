import importlib

def test_validation_imports():
    mod = importlib.import_module('modules.validation')
    assert mod is not None
