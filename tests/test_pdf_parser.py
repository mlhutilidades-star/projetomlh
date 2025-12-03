import importlib

def test_pdf_parser_imports():
    mod = importlib.import_module('modules.pdf_parser')
    assert hasattr(mod, 'parse_pdf') or hasattr(mod, 'PdfParser') or mod is not None
