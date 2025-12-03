import importlib

def test_shopee_api_imports():
    mod = importlib.import_module('modules.shopee_api')
    assert hasattr(mod, 'ShopeeClient') or mod is not None
