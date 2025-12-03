from . import database

def get_rule_for_cnpj(cnpj: str):
    regra = database.get_regra(cnpj)
    if regra and regra.get('ativo'):
        return regra
    return None
