"""
Data validation and normalization utilities
"""
import re
import logging
from datetime import datetime

logger = logging.getLogger('validation')

def normalize_cnpj(cnpj: str) -> str:
    """Normalize CNPJ to standard format XX.XXX.XXX/XXXX-XX"""
    if not cnpj:
        return ''
    
    # Remove tudo exceto dígitos
    digits = re.sub(r'\D', '', cnpj)
    
    if len(digits) != 14:
        logger.warning(f'CNPJ inválido (não tem 14 dígitos): {cnpj}')
        return cnpj  # Return original if invalid
    
    # Formato: 12.345.678/0001-99
    formatted = f"{digits[0:2]}.{digits[2:5]}.{digits[5:8]}/{digits[8:12]}-{digits[12:14]}"
    return formatted

def clean_cnpj(cnpj: str) -> str:
    """Remove formatting from CNPJ, return only digits"""
    if not cnpj:
        return ''
    return re.sub(r'\D', '', cnpj)

def validate_cnpj(cnpj: str) -> bool:
    """Basic CNPJ validation (length check)"""
    digits = clean_cnpj(cnpj)
    return len(digits) == 14

def parse_valor(valor_str: str) -> float:
    """Parse Brazilian currency format to float"""
    if not valor_str:
        return 0.0
    
    try:
        # Remove R$ e espaços
        clean = valor_str.replace('R$', '').strip()
        # Remove pontos de milhar
        clean = clean.replace('.', '')
        # Troca vírgula por ponto
        clean = clean.replace(',', '.')
        return float(clean)
    except Exception as e:
        logger.warning(f'Erro ao parsear valor: {valor_str} - {e}')
        return 0.0

def parse_date_br(date_str: str) -> datetime:
    """Parse Brazilian date format DD/MM/YYYY"""
    if not date_str:
        return None
    
    try:
        return datetime.strptime(date_str, '%d/%m/%Y')
    except Exception as e:
        logger.warning(f'Erro ao parsear data: {date_str} - {e}')
        return None

def detect_duplicate_conta(db, fornecedor: str, valor: float, vencimento, tolerance_days=3):
    """Check if similar conta already exists (duplicate detection)"""
    from modules.database import ContaPagar
    from datetime import timedelta
    
    if not fornecedor or not vencimento:
        return None
    
    # Busca contas com mesmo fornecedor e valor similar em janela de +/- tolerance_days
    start_date = vencimento - timedelta(days=tolerance_days)
    end_date = vencimento + timedelta(days=tolerance_days)
    
    similar = db.query(ContaPagar).filter(
        ContaPagar.fornecedor == fornecedor,
        ContaPagar.valor.between(valor * 0.99, valor * 1.01),  # 1% tolerance
        ContaPagar.vencimento.between(start_date, end_date)
    ).first()
    
    return similar
