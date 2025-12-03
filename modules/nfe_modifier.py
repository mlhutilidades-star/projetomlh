"""
Módulo para modificar XML de NF-e substituindo valores unitários por custos calculados.
"""
import xml.etree.ElementTree as ET
from xml.dom import minidom
import re
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)


def modificar_xml_nfe_com_custos(xml_str: str, custos_por_sku: Dict[str, float]) -> str:
    """
    Modifica XML de NF-e substituindo vUnCom (valor unitário) pelos custos calculados.
    Preserva EXATAMENTE a estrutura original, incluindo declaração XML e formatação.
    
    Args:
        xml_str: String contendo XML da NF-e
        custos_por_sku: Dict mapeando SKU -> custo calculado
    
    Returns:
        String com XML modificado
    """
    try:
        # Preservar declaração XML original
        xml_declaration = ""
        if xml_str.strip().startswith('<?xml'):
            match = re.match(r'<\?xml[^>]+\?>', xml_str.strip())
            if match:
                xml_declaration = match.group(0)
        
        # Parse XML preservando estrutura
        root = ET.fromstring(xml_str.encode('utf-8'))
        
        # Namespace NFe (detectar prefixo automaticamente)
        # O XML pode usar ns0:, nfe:, ou sem prefixo
        ns = {'ns': 'http://www.portalfiscal.inf.br/nfe'}
        
        # Encontrar todos os itens (usar namespace genérico)
        itens = root.findall('.//{http://www.portalfiscal.inf.br/nfe}det')
        modificados = 0
        
        logger.info(f"DEBUG: Encontrados {len(itens)} itens no XML")
        logger.info(f"DEBUG: Dicionário custos tem {len(custos_por_sku)} chaves: {list(custos_por_sku.keys())}")
        
        for item in itens:
            # Pegar código do produto (cProd é obrigatório, sempre existe)
            cod_elem = item.find('.//{http://www.portalfiscal.inf.br/nfe}cProd')
            if cod_elem is None:
                logger.warning("Item sem cProd encontrado!")
                continue
            
            codigo = cod_elem.text.strip() if cod_elem.text else ""
            logger.info(f"DEBUG: Processando item com código '{codigo}'")
            
            # Verificar se temos custo calculado para este código
            if codigo not in custos_por_sku:
                logger.warning(f"Código '{codigo}' não encontrado no dicionário custos_por_sku")
                logger.warning(f"DEBUG: Chaves disponíveis: {list(custos_por_sku.keys())}")
                continue
            
            custo = custos_por_sku[codigo]
            logger.info(f"DEBUG: Custo encontrado para '{codigo}': {custo}")
            
            # Substituir vUnCom (valor unitário comercial)
            vun_elem = item.find('.//{http://www.portalfiscal.inf.br/nfe}vUnCom')
            if vun_elem is not None:
                valor_original = vun_elem.text
                vun_elem.text = f"{custo:.4f}"  # Formato com 4 casas decimais
                logger.info(f"Código {codigo}: vUnCom {valor_original} → {custo:.4f}")
                modificados += 1
            
            # Substituir vUnTrib também (deve ser igual a vUnCom)
            vuntrib_elem = item.find('.//{http://www.portalfiscal.inf.br/nfe}vUnTrib')
            if vuntrib_elem is not None:
                vuntrib_elem.text = f"{custo:.4f}"
            
            # Recalcular vProd (valor total) = vUnCom * qCom
            qcom_elem = item.find('.//{http://www.portalfiscal.inf.br/nfe}qCom')
            vprod_elem = item.find('.//{http://www.portalfiscal.inf.br/nfe}vProd')
            
            if qcom_elem is not None and vprod_elem is not None:
                qtd = float(qcom_elem.text)
                novo_vprod = custo * qtd
                vprod_elem.text = f"{novo_vprod:.2f}"
                logger.info(f"Código {codigo}: vProd recalculado = {novo_vprod:.2f}")
        
        logger.info(f"XML modificado: {modificados} itens alterados")
        
        # Converter de volta para string PRESERVANDO ESTRUTURA
        xml_bytes = ET.tostring(root, encoding='utf-8', method='xml')
        xml_modified = xml_bytes.decode('utf-8')
        
        # Adicionar declaração XML se existia
        if xml_declaration:
            xml_modified = xml_declaration + '\n' + xml_modified
        
        return xml_modified
    
    except Exception as e:
        logger.error(f"Erro ao modificar XML: {e}")
        raise
