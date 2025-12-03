"""Teste rápido para verificar extração de SKU do XML"""
import sys
sys.path.insert(0, r'c:\Users\lemop\Desktop\HUB-FINANCEIRO-STREAMLIT')

from modules.nfe_parser import parse_nfe_xml, to_rows

# Teste com um XML de exemplo (você pode substituir pelo caminho real)
# xml_path = r"caminho\para\seu\arquivo.xml"

print("=" * 60)
print("TESTE DE EXTRAÇÃO DE SKU")
print("=" * 60)

# Simular importação
try:
    from modules.nfe_parser import NFeItem
    
    # Verificar se o dataclass tem o campo sku
    import inspect
    fields = [f.name for f in NFeItem.__dataclass_fields__.values()]
    print(f"\n✓ Campos do NFeItem: {fields}")
    
    if 'sku' in fields:
        print("✓ Campo 'sku' existe no dataclass NFeItem")
    else:
        print("✗ Campo 'sku' NÃO existe no dataclass NFeItem")
    
    # Verificar to_rows
    print("\n" + "=" * 60)
    print("Verificando função to_rows...")
    import inspect
    source = inspect.getsource(to_rows)
    if "'sku':" in source or '"sku":' in source:
        print("✓ Função to_rows inclui 'sku' no dicionário de saída")
    else:
        print("✗ Função to_rows NÃO inclui 'sku' no dicionário")
    
except Exception as e:
    print(f"✗ Erro ao importar: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 60)
print("INSTRUÇÕES:")
print("1. Se o campo 'sku' existe mas não aparece na UI:")
print("   → Reinicie o Streamlit (Ctrl+C no terminal e rode novamente)")
print("2. Se o campo 'sku' não existe:")
print("   → Verifique se as mudanças foram salvas em nfe_parser.py")
print("=" * 60)
