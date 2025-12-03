"""
Módulo para gerar XML NF-e completo compatível com Tiny ERP.
Baseado na estrutura validada que já funciona com a API do Tiny.
"""
import xml.etree.ElementTree as ET
from xml.dom import minidom
from typing import Dict, List, Any
from datetime import datetime
from pathlib import Path
import json
import logging

logger = logging.getLogger(__name__)


def _prefer_value(*values, default='') -> str:
    """Retorna o primeiro valor não vazio dentre os fornecidos."""
    for value in values:
        if value is None:
            continue
        if isinstance(value, str):
            trimmed = value.strip()
            if trimmed:
                return trimmed
        elif value:
            return str(value)
    return default


def _carregar_config() -> Dict[str, Any]:
    """Carrega configuração do arquivo ou retorna padrão"""
    config_file = Path("data/nfe_config.json")
    if config_file.exists():
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"Erro ao carregar config NF-e: {e}, usando padrão")
    return _config_padrao()


def gerar_nfe_completa(
    nfe_original: Any,  # NFeDoc do parser
    custos_por_sku: Dict[str, float],
    config_empresa: Dict[str, Any] = None
) -> str:
    """
    Gera XML NF-e completo com custos calculados, seguindo padrão compatível com Tiny.
    
    Args:
        nfe_original: Objeto NFeDoc com dados da nota original
        custos_por_sku: Dict {SKU: custo_calculado}
        config_empresa: Configurações de emitente/destinatário (opcional, carrega de arquivo)
    
    Returns:
        String com XML formatado pronto para envio ao Tiny
    """
    
    # Carregar configuração do arquivo se não fornecida
    if config_empresa is None:
        config_empresa = _carregar_config()
    
    # Criar root com namespace idêntico ao script legado
    nfe_proc = ET.Element('nfeProc', xmlns="http://www.portalfiscal.inf.br/nfe", versao="4.00")
    NFe = ET.SubElement(nfe_proc, 'NFe', xmlns="http://www.portalfiscal.inf.br/nfe")
    
    # Gerar ID da NF-e (usa chave original quando existir)
    nfe_id = f"NFe{nfe_original.chave}" if getattr(nfe_original, 'chave', '') else "NFe"
    infNFe = ET.SubElement(NFe, 'infNFe', versao="4.00", Id=nfe_id)
    
    # 1. IDE - Identificação
    _adicionar_ide(infNFe, nfe_original, config_empresa)
    
    # 2. EMIT - Emitente (usar dados do XML original + config)
    _adicionar_emit(infNFe, nfe_original, config_empresa)
    
    # 3. DEST - Destinatário (usar dados do XML original + config)
    _adicionar_dest(infNFe, nfe_original, config_empresa)
    
    # 4. DET - Detalhamento dos produtos
    totais = _adicionar_produtos(infNFe, nfe_original.itens, custos_por_sku, config_empresa)
    
    # 5. TOTAL - Totalizadores
    _adicionar_totais(infNFe, totais)
    
    # 6. TRANSP - Transporte
    _adicionar_transporte(infNFe, config_empresa)
    
    # 7. COBR - Cobrança (duplicatas)
    nNF = nfe_original.numero if hasattr(nfe_original, 'numero') else '1'
    _adicionar_cobranca(infNFe, totais['vNF'], nNF)
    
    # 8. PAG - Pagamento
    _adicionar_pagamento(infNFe, totais['vNF'], config_empresa)
    
    # 9. INFADIC - Informações adicionais
    _adicionar_infadic(infNFe, config_empresa)

    # 10. Responsável técnico
    _adicionar_resp_tecnico(infNFe, config_empresa)
    
    # Converter para string formatada
    xml_str = _formatar_xml(nfe_proc)
    
    logger.info(f"XML NF-e gerada: {len(nfe_original.itens)} itens, total R$ {totais['vNF']:.2f}")
    
    return xml_str


def _config_padrao() -> Dict[str, Any]:
    """Configuração padrão baseada no script validado"""
    return {
        "emit": {
            "CNPJ": "12124596000110",
            "xNome": "ARK BRASIL IMP EXP LTDA",
            "xFant": "ARK BRASIL",
            "enderEmit": {
                "xLgr": "RUA WALDEMIRO FERREIRA DOS SANTOS, SN",
                "nro": "SN",
                "xCpl": "LT 1019 B-1 QD 68",
                "xBairro": "CHACARAS ARCAMPO",
                "cMun": "3301702",
                "xMun": "DUQUE DE CAXIAS",
                "UF": "RJ",
                "CEP": "25251285",
                "cPais": "1058",
                "xPais": "BRASIL",
                "fone": "35534418"
            },
            "IE": "79098027",
            "IM": "04744420",
            "CNAE": "4641903",
            "CRT": "3"
        },
        "dest": {
            "CNPJ": "62468045000142",
            "xNome": "MLH COMERCIO E DISTRIBUICAO",
            "enderDest": {
                "xLgr": "RUA NUNO",
                "nro": "492",
                "xBairro": "OURO VERDE",
                "cMun": "3303500",
                "xMun": "NOVA IGUACU",
                "UF": "RJ",
                "CEP": "26263260",
                "cPais": "1058",
                "xPais": "BRASIL",
                "fone": "021982643677"
            },
            "IE": "15754834",
            "email": "mlhutilidades@gmail.com; mlhutilidadesfinanceiro@gmail.com;",
            "indIEDest": "1"
        },
        "ide": {
            "cUF": "33",
            "cNF": "89587539",
            "natOp": "VENDA",
            "mod": "55",
            "serie": "1",
            "nNF": "33679",
            "tpNF": "1",
            "idDest": "1",
            "cMunFG": "3301702",
            "tpImp": "1",
            "tpEmis": "1",
            "cDV": "6",
            "tpAmb": "1",
            "finNFe": "1",
            "indFinal": "0",
            "indPres": "9",
            "indIntermed": "0",
            "procEmi": "0",
            "verProc": "12.1.2410 | 3.0"
        },
        "transp": {
            "modFrete": "0",
            "transporta": {
                "CNPJ": "50346978000188",
                "xNome": "TRANSFRAGA TRANSPORTE LTDA",
                "IE": "14839810",
                "xEnder": "RUA DO MILHO, 00086",
                "UF": "RJ"
            },
            "vol": {
                "qVol": "9",
                "esp": "CAIXA",
                "pesoL": "66.497",
                "pesoB": "74.190"
            }
        },
        "pag": {
            "indPag": "0",
            "tPag": "16"
        },
        "infAdic": {
            "infAdFisco": "(FCP):Adicional de aliquota - Fundo Estadual de Combate a Pobreza e as Desigualdades Sociais (FECP)",
            "infCpl": "Ped. Nr.: 034014 Cond.Pagto.: A VISTA Vendedor: R M S COMERCIO E REPRESENTACOES LTDA ME"
        },
        "infRespTec": {
            "CNPJ": "53113791000122",
            "xContato": "Rodrigo de Almeida Sartorio",
            "email": "resp_tecnico_dfe_protheus@totvs.com.br",
            "fone": "1128593904"
        },
        "impostos": {
            "pICMS": 20.0,
            "pFCP": 2.0,
            "pIPI": 0.0
        },
        "opcoes": {
            "multiplicar_preco": False,
            "multiplicador": 2.0
        }
    }


def _adicionar_ide(infNfe, nfe_original, config):
    """Adiciona bloco IDE (identificação) - ORDEM EXATA conforme schema NF-e"""
    ide = ET.SubElement(infNfe, 'ide')
    
    cfg_ide = config.get('ide', {})
    
    # ORDEM OBRIGATÓRIA do schema NF-e 4.0
    ET.SubElement(ide, 'cUF').text = cfg_ide.get('cUF', '33')
    ET.SubElement(ide, 'cNF').text = cfg_ide.get('cNF', str(abs(hash(datetime.now())) % 100000000))
    ET.SubElement(ide, 'natOp').text = cfg_ide.get('natOp', 'VENDA')
    ET.SubElement(ide, 'mod').text = cfg_ide.get('mod', '55')
    ET.SubElement(ide, 'serie').text = cfg_ide.get('serie', '1')
    ET.SubElement(ide, 'nNF').text = cfg_ide.get('nNF', getattr(nfe_original, 'numero', '1') or '1')

    # Datas: usa config se disponível, senão data/hora atual
    data_emissao = cfg_ide.get('dhEmi') or datetime.now().strftime('%Y-%m-%dT%H:%M:%S-03:00')
    data_saida = cfg_ide.get('dhSaiEnt') or data_emissao
    ET.SubElement(ide, 'dhEmi').text = data_emissao
    ET.SubElement(ide, 'dhSaiEnt').text = data_saida

    ET.SubElement(ide, 'tpNF').text = cfg_ide.get('tpNF', '1')  # 1 = saída
    ET.SubElement(ide, 'idDest').text = cfg_ide.get('idDest', '1')
    ET.SubElement(ide, 'cMunFG').text = cfg_ide.get('cMunFG', '3303500')
    ET.SubElement(ide, 'tpImp').text = cfg_ide.get('tpImp', '1')
    ET.SubElement(ide, 'tpEmis').text = cfg_ide.get('tpEmis', '1')
    ET.SubElement(ide, 'cDV').text = cfg_ide.get('cDV', '0')
    ET.SubElement(ide, 'tpAmb').text = cfg_ide.get('tpAmb', '1')
    ET.SubElement(ide, 'finNFe').text = cfg_ide.get('finNFe', '1')
    ET.SubElement(ide, 'indFinal').text = cfg_ide.get('indFinal', '0')
    ET.SubElement(ide, 'indPres').text = cfg_ide.get('indPres', '9')
    ET.SubElement(ide, 'indIntermed').text = cfg_ide.get('indIntermed', '0')
    ET.SubElement(ide, 'procEmi').text = cfg_ide.get('procEmi', '0')
    ET.SubElement(ide, 'verProc').text = cfg_ide.get('verProc', 'Sistema MLH v1.0')


def _adicionar_emit(infNfe, nfe_original, config):
    """Adiciona bloco EMIT (emitente) usando config (pois parser só tem nome)"""
    emit = ET.SubElement(infNfe, 'emit')
    
    cfg_emit = config.get('emit', {})
    emit_info = getattr(nfe_original, 'emitente_dados', None)

    cnpj_fallback = cfg_emit.get('CNPJ', '00000000000000')
    cnpj = getattr(emit_info, 'cnpj', '') if emit_info else ''
    cpf = getattr(emit_info, 'cpf', '') if emit_info else ''
    if cnpj:
        ET.SubElement(emit, 'CNPJ').text = cnpj
    elif cpf:
        ET.SubElement(emit, 'CPF').text = cpf
    else:
        ET.SubElement(emit, 'CNPJ').text = cnpj_fallback

    nome_emit = _prefer_value(
        getattr(emit_info, 'xNome', '') if emit_info else '',
        nfe_original.emitente,
        cfg_emit.get('xNome', ''),
        default='EMITENTE'
    )
    fantasia_emit = _prefer_value(
        getattr(emit_info, 'xFant', '') if emit_info else '',
        nome_emit,
        cfg_emit.get('xFant', ''),
        default='EMITENTE'
    )
    ET.SubElement(emit, 'xNome').text = nome_emit
    ET.SubElement(emit, 'xFant').text = fantasia_emit

    # Endereço
    enderEmit = ET.SubElement(emit, 'enderEmit')
    end_cfg = cfg_emit.get('enderEmit', {})
    end_info = getattr(emit_info, 'endereco', None)

    def end_value(attr, fallback):
        if end_info is not None:
            valor = getattr(end_info, attr, '')
            if valor:
                return valor
        return end_cfg.get(attr, fallback)

    ET.SubElement(enderEmit, 'xLgr').text = end_value('xLgr', 'RUA')
    ET.SubElement(enderEmit, 'nro').text = end_value('nro', 'SN')
    xCpl_value = end_value('xCpl', '')
    if xCpl_value:
        ET.SubElement(enderEmit, 'xCpl').text = xCpl_value
    ET.SubElement(enderEmit, 'xBairro').text = end_value('xBairro', 'CENTRO')
    ET.SubElement(enderEmit, 'cMun').text = end_value('cMun', '3303500')
    ET.SubElement(enderEmit, 'xMun').text = end_value('xMun', 'NOVA IGUACU')
    ET.SubElement(enderEmit, 'UF').text = end_value('UF', 'RJ')
    ET.SubElement(enderEmit, 'CEP').text = end_value('CEP', '00000000')
    ET.SubElement(enderEmit, 'cPais').text = end_value('cPais', '1058') or '1058'
    ET.SubElement(enderEmit, 'xPais').text = end_value('xPais', 'BRASIL') or 'BRASIL'

    telefone_emit = _prefer_value(
        getattr(end_info, 'fone', '') if end_info else '',
        getattr(emit_info, 'telefone', '') if emit_info else '',
        end_cfg.get('fone', '')
    )
    if telefone_emit:
        ET.SubElement(enderEmit, 'fone').text = telefone_emit
    
    ET.SubElement(emit, 'IE').text = _prefer_value(
        getattr(emit_info, 'ie', '') if emit_info else '',
        cfg_emit.get('IE', ''),
        default='ISENTO'
    )
    im_value = _prefer_value(
        getattr(emit_info, 'im', '') if emit_info else '',
        cfg_emit.get('IM', '')
    )
    if im_value:
        ET.SubElement(emit, 'IM').text = im_value
    cnae_value = _prefer_value(cfg_emit.get('CNAE', ''))
    if cnae_value:
        ET.SubElement(emit, 'CNAE').text = cnae_value
    ET.SubElement(emit, 'CRT').text = _prefer_value(
        getattr(emit_info, 'crt', '') if emit_info else '',
        cfg_emit.get('CRT', ''),
        default='1'
    )


def _adicionar_dest(infNfe, nfe_original, config):
    """Adiciona bloco DEST (destinatário) usando config (pois parser só tem nome)"""
    dest = ET.SubElement(infNfe, 'dest')
    
    cfg_dest = config.get('dest', {})
    dest_info = getattr(nfe_original, 'destinatario_dados', None)

    cnpj_dest = getattr(dest_info, 'cnpj', '') if dest_info else ''
    cpf_dest = getattr(dest_info, 'cpf', '') if dest_info else ''
    if cnpj_dest:
        ET.SubElement(dest, 'CNPJ').text = cnpj_dest
    elif cpf_dest:
        ET.SubElement(dest, 'CPF').text = cpf_dest
    else:
        ET.SubElement(dest, 'CNPJ').text = cfg_dest.get('CNPJ', '00000000000000')
    ET.SubElement(dest, 'xNome').text = _prefer_value(
        getattr(dest_info, 'xNome', '') if dest_info else '',
        nfe_original.destinatario,
        cfg_dest.get('xNome', ''),
        default='DESTINATARIO'
    )
    
    # Endereço
    enderDest = ET.SubElement(dest, 'enderDest')
    end_cfg = cfg_dest.get('enderDest', {})
    end_info = getattr(dest_info, 'endereco', None)

    def dest_end(attr, fallback):
        if end_info is not None:
            valor = getattr(end_info, attr, '')
            if valor:
                return valor
        return end_cfg.get(attr, fallback)

    ET.SubElement(enderDest, 'xLgr').text = dest_end('xLgr', 'RUA')
    ET.SubElement(enderDest, 'nro').text = dest_end('nro', 'SN')
    xBairro = dest_end('xBairro', 'CENTRO')
    ET.SubElement(enderDest, 'xBairro').text = xBairro
    ET.SubElement(enderDest, 'cMun').text = dest_end('cMun', '3303500')
    ET.SubElement(enderDest, 'xMun').text = dest_end('xMun', 'NOVA IGUACU')
    ET.SubElement(enderDest, 'UF').text = dest_end('UF', 'RJ')
    ET.SubElement(enderDest, 'CEP').text = dest_end('CEP', '00000000')
    ET.SubElement(enderDest, 'cPais').text = dest_end('cPais', '1058') or '1058'
    ET.SubElement(enderDest, 'xPais').text = dest_end('xPais', 'BRASIL') or 'BRASIL'

    telefone_dest = _prefer_value(
        getattr(end_info, 'fone', '') if end_info else '',
        getattr(dest_info, 'telefone', '') if dest_info else '',
        end_cfg.get('fone', '')
    )
    if telefone_dest:
        ET.SubElement(enderDest, 'fone').text = telefone_dest
    
    # indIEDest FORA de enderDest
    ET.SubElement(dest, 'indIEDest').text = _prefer_value(
        getattr(dest_info, 'indIEDest', '') if dest_info else '',
        cfg_dest.get('indIEDest', ''),
        default='1'
    )

    ie_dest = _prefer_value(
        getattr(dest_info, 'ie', '') if dest_info else '',
        cfg_dest.get('IE', '')
    )
    if ie_dest:
        ET.SubElement(dest, 'IE').text = ie_dest
    email_dest = _prefer_value(
        getattr(dest_info, 'email', '') if dest_info else '',
        cfg_dest.get('email', '')
    )
    if email_dest:
        ET.SubElement(dest, 'email').text = email_dest


def _cfop_saida(cfop_original: str) -> str:
    """Converte CFOP de entrada para a CFOP de saída equivalente."""
    if not cfop_original:
        return '5102'
    cfop_original = cfop_original.strip()
    if len(cfop_original) < 4:
        return '5102'
    mapa = {
        '1': '5',  # dentro do estado
        '2': '6',  # interestadual
        '3': '7',  # exterior
        '5': '5',
        '6': '6',
        '7': '7'
    }
    novo_prefixo = mapa.get(cfop_original[0], '5')
    return novo_prefixo + cfop_original[1:]


def _adicionar_produtos(infNfe, itens, custos_por_sku, config):
    """Adiciona itens (DET) e calcula totais"""
    
    pICMS = config['impostos']['pICMS']
    pFCP = config['impostos']['pFCP']
    pIPI = config['impostos']['pIPI']
    
    totais = {
        'vBC': 0.0,
        'vICMS': 0.0,
        'vFCP': 0.0,
        'vIPI': 0.0,
        'vProd': 0.0,
        'vNF': 0.0
    }
    
    for idx, item in enumerate(itens, start=1):
        det = ET.SubElement(infNfe, 'det', nItem=str(idx))
        
        # Produto
        prod = ET.SubElement(det, 'prod')
        
        # Usar código do produto (cProd) como chave - SEMPRE existe
        codigo = str(item.codigo)
        sku_ean = item.sku if hasattr(item, 'sku') and item.sku else ''
        if not sku_ean or str(sku_ean).upper() in {'SEM GTIN', '0', '0000000000000'}:
            sku_ean = '0000000000000'
        
        ET.SubElement(prod, 'cProd').text = codigo
        ET.SubElement(prod, 'cEAN').text = sku_ean
        ET.SubElement(prod, 'xProd').text = str(item.descricao)
        ncm_val = (item.ncm or '').strip() or '00000000'
        ET.SubElement(prod, 'NCM').text = ncm_val
        ET.SubElement(prod, 'cBenef').text = ''
        ET.SubElement(prod, 'CFOP').text = _cfop_saida(getattr(item, 'cfop', ''))
        unidade = getattr(item, 'unidade', '') or 'PC'
        ET.SubElement(prod, 'uCom').text = unidade
        
        qtd = float(item.quantidade)
        ET.SubElement(prod, 'qCom').text = f"{qtd:.4f}"
        
        # USAR CUSTO CALCULADO - buscar por cProd!
        custo = custos_por_sku.get(codigo, item.vUnCom)
        ET.SubElement(prod, 'vUnCom').text = f"{custo:.10f}"
        
        vProd_item = round(custo * qtd, 2)
        ET.SubElement(prod, 'vProd').text = f"{vProd_item:.2f}"
        
        ET.SubElement(prod, 'cEANTrib').text = sku_ean
        ET.SubElement(prod, 'uTrib').text = unidade
        ET.SubElement(prod, 'qTrib').text = f"{qtd:.4f}"
        ET.SubElement(prod, 'vUnTrib').text = f"{custo:.10f}"
        ET.SubElement(prod, 'indTot').text = '1'
        
        # Impostos - ORDEM EXATA
        imposto = ET.SubElement(det, 'imposto')
        
        # vTotTrib - Valor aproximado dos tributos (simplificado)
        vTotTrib = round(vProd_item * 0.20, 2)  # Aproximado 20%
        ET.SubElement(imposto, 'vTotTrib').text = f"{vTotTrib:.2f}"
        
        # ICMS
        ICMS = ET.SubElement(imposto, 'ICMS')
        ICMS00 = ET.SubElement(ICMS, 'ICMS00')
        ET.SubElement(ICMS00, 'orig').text = '0'
        ET.SubElement(ICMS00, 'CST').text = '00'
        ET.SubElement(ICMS00, 'modBC').text = '3'
        ET.SubElement(ICMS00, 'vBC').text = f"{vProd_item:.2f}"
        ET.SubElement(ICMS00, 'pICMS').text = f"{pICMS:.2f}"
        
        vICMS_item = round(vProd_item * (pICMS / 100), 2)
        ET.SubElement(ICMS00, 'vICMS').text = f"{vICMS_item:.2f}"
        
        # FCP
        ET.SubElement(ICMS00, 'pFCP').text = f"{pFCP:.2f}"
        vFCP_item = round(vProd_item * (pFCP / 100), 2)
        ET.SubElement(ICMS00, 'vFCP').text = f"{vFCP_item:.2f}"
        
        # IPI
        IPI = ET.SubElement(imposto, 'IPI')
        ET.SubElement(IPI, 'cEnq').text = '999'
        IPITrib = ET.SubElement(IPI, 'IPITrib')
        ET.SubElement(IPITrib, 'CST').text = '99'
        ET.SubElement(IPITrib, 'vBC').text = '0.00'
        ET.SubElement(IPITrib, 'pIPI').text = f"{pIPI:.2f}"
        
        vIPI_item = round(vProd_item * (pIPI / 100), 2)
        ET.SubElement(IPITrib, 'vIPI').text = f"{vIPI_item:.2f}"
        
        # PIS/COFINS zerados (estrutura igual ao script legado)
        PIS = ET.SubElement(imposto, 'PIS')
        PISAliq = ET.SubElement(PIS, 'PISAliq')
        ET.SubElement(PISAliq, 'CST').text = '01'
        ET.SubElement(PISAliq, 'vBC').text = '0'
        ET.SubElement(PISAliq, 'pPIS').text = '0'
        ET.SubElement(PISAliq, 'vPIS').text = '0'
        
        COFINS = ET.SubElement(imposto, 'COFINS')
        COFINSAliq = ET.SubElement(COFINS, 'COFINSAliq')
        ET.SubElement(COFINSAliq, 'CST').text = '01'
        ET.SubElement(COFINSAliq, 'vBC').text = '0'
        ET.SubElement(COFINSAliq, 'pCOFINS').text = '0'
        ET.SubElement(COFINSAliq, 'vCOFINS').text = '0'
        
        # Acumular totais
        totais['vBC'] += vProd_item
        totais['vICMS'] += vICMS_item
        totais['vFCP'] += vFCP_item
        totais['vIPI'] += vIPI_item
        totais['vProd'] += vProd_item
        
        # Informação adicional do item destacando o FCP
        infAdProd = ET.SubElement(det, 'infAdProd')
        infAdProd.text = f"(FCP): Base R$ {vProd_item:.2f} Perc.({pFCP:.0f}%) Vlr. R$ {vFCP_item:.2f}"
    
    # Total da NF = vProd (sem somar ICMS, pois já está destacado)
    totais['vNF'] = totais['vProd']
    
    return totais


def _adicionar_totais(infNfe, totais):
    """Adiciona bloco TOTAL"""
    total = ET.SubElement(infNfe, 'total')
    ICMSTot = ET.SubElement(total, 'ICMSTot')
    
    ET.SubElement(ICMSTot, 'vBC').text = f"{totais['vBC']:.2f}"
    ET.SubElement(ICMSTot, 'vICMS').text = f"{totais['vICMS']:.2f}"
    ET.SubElement(ICMSTot, 'vICMSDeson').text = "0.00"
    ET.SubElement(ICMSTot, 'vFCPUFDest').text = "0"
    ET.SubElement(ICMSTot, 'vICMSUFDest').text = "0"
    ET.SubElement(ICMSTot, 'vICMSUFRemet').text = "0"
    ET.SubElement(ICMSTot, 'vFCP').text = f"{totais['vFCP']:.2f}"
    ET.SubElement(ICMSTot, 'vBCST').text = "0.00"
    ET.SubElement(ICMSTot, 'vST').text = "0.00"
    ET.SubElement(ICMSTot, 'vFCPST').text = "0.00"
    ET.SubElement(ICMSTot, 'vFCPSTRet').text = "0"
    ET.SubElement(ICMSTot, 'vProd').text = f"{totais['vProd']:.2f}"
    ET.SubElement(ICMSTot, 'vFrete').text = "0.00"
    ET.SubElement(ICMSTot, 'vSeg').text = "0.00"
    ET.SubElement(ICMSTot, 'vDesc').text = "0.00"
    ET.SubElement(ICMSTot, 'vII').text = "0.00"
    ET.SubElement(ICMSTot, 'vIPI').text = f"{totais['vIPI']:.2f}"
    ET.SubElement(ICMSTot, 'vIPIDevol').text = "0.00"
    ET.SubElement(ICMSTot, 'vPIS').text = "0.00"
    ET.SubElement(ICMSTot, 'vCOFINS').text = "0.00"
    ET.SubElement(ICMSTot, 'vOutro').text = "0.00"
    ET.SubElement(ICMSTot, 'vNF').text = f"{totais['vNF']:.2f}"


def _adicionar_transporte(infNfe, config):
    """Adiciona bloco TRANSP (simplificado)"""
    transp_cfg = config.get('transp', {})
    transp = ET.SubElement(infNfe, 'transp')
    ET.SubElement(transp, 'modFrete').text = transp_cfg.get('modFrete', '0')

    transporta_cfg = transp_cfg.get('transporta', {})
    if transporta_cfg:
        transporta = ET.SubElement(transp, 'transporta')
        if transporta_cfg.get('CNPJ'):
            ET.SubElement(transporta, 'CNPJ').text = transporta_cfg.get('CNPJ')
        if transporta_cfg.get('xNome'):
            ET.SubElement(transporta, 'xNome').text = transporta_cfg.get('xNome')
        if transporta_cfg.get('IE'):
            ET.SubElement(transporta, 'IE').text = transporta_cfg.get('IE')
        if transporta_cfg.get('xEnder'):
            ET.SubElement(transporta, 'xEnder').text = transporta_cfg.get('xEnder')
        if transporta_cfg.get('UF'):
            ET.SubElement(transporta, 'UF').text = transporta_cfg.get('UF')

    vol_cfg = transp_cfg.get('vol', {})
    if vol_cfg:
        vol = ET.SubElement(transp, 'vol')
        if vol_cfg.get('qVol'):
            ET.SubElement(vol, 'qVol').text = vol_cfg.get('qVol')
        if vol_cfg.get('esp'):
            ET.SubElement(vol, 'esp').text = vol_cfg.get('esp')
        if vol_cfg.get('pesoL'):
            ET.SubElement(vol, 'pesoL').text = vol_cfg.get('pesoL')
        if vol_cfg.get('pesoB'):
            ET.SubElement(vol, 'pesoB').text = vol_cfg.get('pesoB')


def _adicionar_cobranca(infNfe, vNF, nNF):
    """Adiciona bloco COBR (cobrança)"""
    cobr = ET.SubElement(infNfe, 'cobr')
    
    # Fatura
    ET.SubElement(cobr, 'nFat').text = str(nNF)
    ET.SubElement(cobr, 'vOrig').text = f"{vNF:.2f}"
    ET.SubElement(cobr, 'vLiq').text = f"{vNF:.2f}"
    
    # Duplicata
    dup = ET.SubElement(cobr, 'dup')
    ET.SubElement(dup, 'nDup').text = '001'
    ET.SubElement(dup, 'vDup').text = f"{vNF:.2f}"


def _adicionar_pagamento(infNfe, vNF, config):
    """Adiciona bloco PAG"""
    pag = ET.SubElement(infNfe, 'pag')
    detPag = ET.SubElement(pag, 'detPag')
    
    cfg_pag = config.get('pag', {})
    ind_pag = cfg_pag.get('indPag')
    if ind_pag is not None:
        ET.SubElement(detPag, 'indPag').text = ind_pag
    ET.SubElement(detPag, 'tPag').text = cfg_pag.get('tPag', '99')  # 99 = Outros
    ET.SubElement(detPag, 'vPag').text = f"{vNF:.2f}"


def _adicionar_infadic(infNfe, config):
    """Adiciona informações adicionais"""
    infAdic = ET.SubElement(infNfe, 'infAdic')
    
    cfg = config.get('infAdic', {})
    inf_ad_fisco = cfg.get('infAdFisco')
    if inf_ad_fisco:
        ET.SubElement(infAdic, 'infAdFisco').text = inf_ad_fisco
    ET.SubElement(infAdic, 'infCpl').text = cfg.get(
        'infCpl',
        'NF-e gerada com custos calculados por regras personalizadas. Sistema MLH Hub Financeiro.'
    )


def _adicionar_resp_tecnico(infNfe, config):
    """Adiciona bloco do responsável técnico"""
    cfg = config.get('infRespTec', {})
    if not cfg:
        return
    infRespTec = ET.SubElement(infNfe, 'infRespTec')
    if cfg.get('CNPJ'):
        ET.SubElement(infRespTec, 'CNPJ').text = cfg.get('CNPJ')
    if cfg.get('xContato'):
        ET.SubElement(infRespTec, 'xContato').text = cfg.get('xContato')
    if cfg.get('email'):
        ET.SubElement(infRespTec, 'email').text = cfg.get('email')
    if cfg.get('fone'):
        ET.SubElement(infRespTec, 'fone').text = cfg.get('fone')


def _formatar_xml(element):
    """Formata XML com indentação"""
    rough_string = ET.tostring(element, encoding='unicode')
    reparsed = minidom.parseString(rough_string)
    return reparsed.toprettyxml(indent="  ", encoding="UTF-8").decode('utf-8')
