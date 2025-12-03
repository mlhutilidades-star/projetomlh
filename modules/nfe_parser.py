"""NFe XML parser for extracting item details and computing suggested costs.

This module focuses on NF-e (Brazil) XML files. It extracts:
- itens: codigo (cProd), descricao (xProd), ncm, cfop, quantidade (qCom),
  valor unit (vUnCom), valor total (vProd), impostos (IPI, ST, ICMS, PIS, COFINS),
  and totals (frete, seguro, desconto, outros) from the invoice to allow
  cost allocation per item.

We compute a suggested unit cost with a configurable rule:
  custo_sugerido_unit = base_unit + rateio_frete + rateio_seguro + rateio_outros - rateio_desconto + ipi_unit + st_unit

Notes:
- XML fields are decimals in string; we'll parse safely.
- Some taxes may be absent depending on regime. We'll treat missing as zero.
- The allocation bases by default are proportional to item vProd.
"""
from __future__ import annotations
import xml.etree.ElementTree as ET
from dataclasses import dataclass, asdict, field
from typing import List, Dict, Any, Optional


def _sf(s: Optional[str]) -> float:
    if s is None:
        return 0.0
    try:
        return float(str(s).replace(',', '.'))
    except Exception:
        return 0.0

@dataclass
class NFeEndereco:
    xLgr: str = ''
    nro: str = ''
    xCpl: str = ''
    xBairro: str = ''
    cMun: str = ''
    xMun: str = ''
    UF: str = ''
    CEP: str = ''
    cPais: str = ''
    xPais: str = ''
    fone: str = ''


@dataclass
class NFeParte:
    cnpj: str = ''
    cpf: str = ''
    xNome: str = ''
    xFant: str = ''
    ie: str = ''
    im: str = ''
    crt: str = ''
    indIEDest: str = ''
    email: str = ''
    telefone: str = ''
    endereco: NFeEndereco = field(default_factory=NFeEndereco)


@dataclass
class NFeItem:
    codigo: str
    descricao: str
    ncm: str
    cfop: str
    quantidade: float
    vUnCom: float
    vProd: float
    ipi: float
    ipi_aliq: float
    st: float
    icms: float
    pis: float
    cofins: float
    sku: str = ''  # GTIN/EAN (cEAN ou cEANTrib)
    rateio_frete: float = 0.0
    rateio_seguro: float = 0.0
    rateio_outros: float = 0.0
    rateio_desconto: float = 0.0
    custo_sugerido_unit: float = 0.0

@dataclass
class NFeDoc:
    numero: str
    serie: str
    chave: str
    emitente: str
    destinatario: str
    vFrete: float
    vSeguro: float
    vDesc: float
    vOutro: float
    itens: List[NFeItem]
    modelo: str = '55'  # Modelo da nota (55=NF-e, 65=NFC-e)
    finalidade: str = '1'  # 1=Normal, 2=Complementar, 3=Ajuste, 4=Devolução
    emitente_dados: NFeParte = field(default_factory=NFeParte)
    destinatario_dados: NFeParte = field(default_factory=NFeParte)


def parse_nfe_xml(path: str) -> NFeDoc:
    tree = ET.parse(path)
    root = tree.getroot()

    # Detectar namespace automaticamente
    ns = {}
    if root.tag.startswith('{'):
        namespace = root.tag.split('}')[0].strip('{')
        ns = {'nfe': namespace}
    
    # Função helper para buscar com/sem namespace
    def find_elem(parent, tag):
        if ns:
            return parent.find(f'.//nfe:{tag}', ns)
        return parent.find(f'.//{tag}')
    
    def findtext_elem(parent, tag, default=''):
        """Find text for a tag under parent, searching recursively (descendants).
        Works with or without namespace and is robust to nested nodes like IPITrib/ICMS00.
        """
        if parent is None:
            return default
        if ns:
            # search recursively
            node = parent.find(f'.//nfe:{tag}', ns)
            return node.text if node is not None and node.text is not None else default
        else:
            node = parent.find(f'.//{tag}')
            return node.text if node is not None and node.text is not None else default

    ide = find_elem(root, 'ide')
    emit = find_elem(root, 'emit')
    dest = find_elem(root, 'dest')
    total = find_elem(root, 'ICMSTot')

    numero = (findtext_elem(ide, 'nNF') if ide is not None else '')
    serie = (findtext_elem(ide, 'serie') if ide is not None else '')
    modelo = (findtext_elem(ide, 'mod') if ide is not None else '55')
    finalidade = (findtext_elem(ide, 'finNFe') if ide is not None else '1')
    
    # Chave da NF-e
    chave = ''
    infnfe = find_elem(root, 'infNFe')
    if infnfe is not None:
        chave = infnfe.attrib.get('Id','').replace('NFe','')

    def parse_endereco(node) -> NFeEndereco:
        if node is None:
            return NFeEndereco()
        return NFeEndereco(
            xLgr=findtext_elem(node, 'xLgr', ''),
            nro=findtext_elem(node, 'nro', ''),
            xCpl=findtext_elem(node, 'xCpl', ''),
            xBairro=findtext_elem(node, 'xBairro', ''),
            cMun=findtext_elem(node, 'cMun', ''),
            xMun=findtext_elem(node, 'xMun', ''),
            UF=findtext_elem(node, 'UF', ''),
            CEP=findtext_elem(node, 'CEP', ''),
            cPais=findtext_elem(node, 'cPais', ''),
            xPais=findtext_elem(node, 'xPais', ''),
            fone=findtext_elem(node, 'fone', ''),
        )

    def parse_parte(node, tipo: str) -> NFeParte:
        if node is None:
            return NFeParte()
        endereco_tag = 'enderEmit' if tipo == 'emit' else 'enderDest'
        endereco = parse_endereco(find_elem(node, endereco_tag))
        parte = NFeParte(
            cnpj=findtext_elem(node, 'CNPJ', ''),
            cpf=findtext_elem(node, 'CPF', ''),
            xNome=findtext_elem(node, 'xNome', ''),
            xFant=findtext_elem(node, 'xFant', ''),
            ie=findtext_elem(node, 'IE', ''),
            im=findtext_elem(node, 'IM', ''),
            crt=findtext_elem(node, 'CRT', '') if tipo == 'emit' else '',
            indIEDest=findtext_elem(node, 'indIEDest', '') if tipo == 'dest' else '',
            email=findtext_elem(node, 'email', ''),
            telefone=findtext_elem(node, 'fone', ''),
        )
        if not parte.xFant:
            parte.xFant = parte.xNome
        parte.endereco = endereco
        return parte

    emit_data = parse_parte(emit, 'emit')
    dest_data = parse_parte(dest, 'dest')

    emitente = emit_data.xNome
    destinatario = dest_data.xNome

    vFrete = _sf(findtext_elem(total, 'vFrete', '0')) if total is not None else 0.0
    vSeguro = _sf(findtext_elem(total, 'vSeg', '0')) if total is not None else 0.0
    vDesc = _sf(findtext_elem(total, 'vDesc', '0')) if total is not None else 0.0
    vOutro = _sf(findtext_elem(total, 'vOutro', '0')) if total is not None else 0.0

    itens: List[NFeItem] = []
    if ns:
        dets = root.findall('.//nfe:det', ns)
    else:
        dets = root.findall('.//det')
    
    soma_vProd = 0.0
    for det in dets:
        prod = find_elem(det, 'prod')
        imp = find_elem(det, 'imposto')
        if prod is None:
            continue
        codigo = findtext_elem(prod, 'cProd')
        descricao = findtext_elem(prod, 'xProd')
        ncm = findtext_elem(prod, 'NCM')
        cfop = findtext_elem(prod, 'CFOP')
        quantidade = _sf(findtext_elem(prod, 'qCom', '0'))
        vUnCom = _sf(findtext_elem(prod, 'vUnCom', '0'))
        vProd = _sf(findtext_elem(prod, 'vProd', '0'))
        quantidade = _sf(prod.findtext('nfe:qCom', default='0', namespaces=ns))
        vUnCom = _sf(prod.findtext('nfe:vUnCom', default='0', namespaces=ns))
        vProd = _sf(prod.findtext('nfe:vProd', default='0', namespaces=ns))
        
        # Extrair SKU (GTIN/EAN): cEAN prioritário, fallback cEANTrib
        sku = findtext_elem(prod, 'cEAN', '').strip()
        if not sku or sku.upper() in ('SEM GTIN', '0000000000000', '0'):
            sku = findtext_elem(prod, 'cEANTrib', '').strip()
        if sku.upper() in ('SEM GTIN', '0000000000000', '0'):
            sku = ''
        
        soma_vProd += vProd

        ipi = 0.0
        ipi_aliq = 0.0
        st = 0.0
        icms = 0.0
        pis = 0.0
        cofins = 0.0
        if imp is not None:
            ipi_node = find_elem(imp, 'IPI')
            if ipi_node is not None:
                ipi = _sf(findtext_elem(ipi_node, 'vIPI', '0'))
                ipi_aliq = _sf(findtext_elem(ipi_node, 'pIPI', '0'))
            icms_node = find_elem(imp, 'ICMS')
            if icms_node is not None:
                st = _sf(findtext_elem(icms_node, 'vICMSST', '0'))
                icms = _sf(findtext_elem(icms_node, 'vICMS', '0'))
            pis_node = find_elem(imp, 'PIS')
            if pis_node is not None:
                pis = _sf(findtext_elem(pis_node, 'vPIS', '0'))
            cof_node = find_elem(imp, 'COFINS')
            if cof_node is not None:
                cofins = _sf(findtext_elem(cof_node, 'vCOFINS', '0'))

        itens.append(NFeItem(
            codigo=codigo, descricao=descricao, ncm=ncm, cfop=cfop,
            quantidade=quantidade, vUnCom=vUnCom, vProd=vProd,
            ipi=ipi, ipi_aliq=ipi_aliq, st=st, icms=icms, pis=pis, cofins=cofins,
            sku=sku
        ))

    # Allocations proportional to vProd
    for it in itens:
        base = it.vProd / soma_vProd if soma_vProd > 0 else 0.0
        it.rateio_frete = vFrete * base
        it.rateio_seguro = vSeguro * base
        it.rateio_outros = vOutro * base
        it.rateio_desconto = vDesc * base
        total_rateios = it.rateio_frete + it.rateio_seguro + it.rateio_outros - it.rateio_desconto
        ipi_unit = (it.ipi / it.quantidade) if it.quantidade else 0.0
        st_unit = (it.st / it.quantidade) if it.quantidade else 0.0
        rateio_unit = (total_rateios / it.quantidade) if it.quantidade else 0.0
        it.custo_sugerido_unit = it.vUnCom + rateio_unit + ipi_unit + st_unit

    return NFeDoc(
        numero=numero, serie=serie, chave=chave, emitente=emitente, destinatario=destinatario,
        vFrete=vFrete, vSeguro=vSeguro, vDesc=vDesc, vOutro=vOutro, itens=itens,
        modelo=modelo, finalidade=finalidade,
        emitente_dados=emit_data, destinatario_dados=dest_data
    )


def to_rows(nfe: NFeDoc) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for it in nfe.itens:
        rows.append({
            'codigo': it.codigo,
            'sku': it.sku,
            'descricao': it.descricao,
            'ncm': it.ncm,
            'cfop': it.cfop,
            'quantidade': it.quantidade,
            'vUnCom': it.vUnCom,
            'vProd': it.vProd,
            'ipi_total': it.ipi,
            'ipi_aliq': it.ipi_aliq,
            'st_total': it.st,
            'icms_total': it.icms,
            'pis_total': it.pis,
            'cofins_total': it.cofins,
            'rateio_frete': it.rateio_frete,
            'rateio_seguro': it.rateio_seguro,
            'rateio_outros': it.rateio_outros,
            'rateio_desconto': it.rateio_desconto,
            'custo_unit_sugerido': it.custo_sugerido_unit,
            'custo_unit_final': it.custo_sugerido_unit,  # editable by user
        })
    return rows
