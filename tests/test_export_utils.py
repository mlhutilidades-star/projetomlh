import importlib

def test_export_utils_imports():
    mod = importlib.import_module('modules.export_utils')
    assert mod is not None
