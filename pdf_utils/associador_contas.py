from typing import List, Dict

def associar_dados_com_contas(dados_extraidos: List[str], contas_existentes: List[Dict]) -> List[Dict]:
    """
    Associa dados extraídos de PDFs com contas existentes.

    :param dados_extraidos: Lista de strings com os dados extraídos.
    :param contas_existentes: Lista de dicionários representando contas existentes.
    :return: Lista de dicionários com as contas atualizadas.
    """
    contas_atualizadas = []

    for conta in contas_existentes:
        for dado in dados_extraidos:
            if conta['identificador'] in dado:
                conta['dados_extras'] = dado
                contas_atualizadas.append(conta)

    return contas_atualizadas
