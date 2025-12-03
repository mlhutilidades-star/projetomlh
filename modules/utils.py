def format_currency(value: float) -> str:
    return f"R$ {value:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')

import re

def clean_cnpj(cnpj: str) -> str:
    return re.sub(r'\D','', cnpj or '')
