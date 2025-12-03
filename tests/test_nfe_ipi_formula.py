import os
import tempfile
from modules.nfe_parser import parse_nfe_xml
from modules.regras_custo import RegraFornecedorCusto

# Minimal NF-e XML with namespace and one item
NFE_XML_WITH_PIPI = """<?xml version="1.0" encoding="UTF-8"?>
<nfeProc xmlns="http://www.portalfiscal.inf.br/nfe">
  <NFe>
    <infNFe Id="NFe35191111111111111111550010000000011000000010" versao="4.00">
      <ide>
        <nNF>12345</nNF>
        <serie>1</serie>
      </ide>
      <emit>
        <xNome>FORNECEDOR TESTE LTDA</xNome>
      </emit>
      <dest>
        <xNome>DESTINATARIO TESTE</xNome>
      </dest>
      <det nItem="1">
        <prod>
          <cProd>001</cProd>
          <xProd>Produto de Teste</xProd>
          <NCM>00000000</NCM>
          <CFOP>5101</CFOP>
          <qCom>60.0000</qCom>
          <vUnCom>2.3330</vUnCom>
          <vProd>139.98</vProd>
        </prod>
        <imposto>
          <IPI>
            <IPITrib>
              <CST>50</CST>
              <vBC>139.98</vBC>
              <pIPI>6.50</pIPI>
              <vIPI>9.10</vIPI>
            </IPITrib>
          </IPI>
        </imposto>
      </det>
      <total>
        <ICMSTot>
          <vFrete>0.00</vFrete>
          <vSeg>0.00</vSeg>
          <vDesc>0.00</vDesc>
          <vOutro>0.00</vOutro>
        </ICMSTot>
      </total>
    </infNFe>
  </NFe>
</nfeProc>
"""

# Same XML but without pIPI tag to trigger fallback from vIPI/vProd
NFE_XML_WITHOUT_PIPI = NFE_XML_WITH_PIPI.replace("<pIPI>6.50</pIPI>\n              ", "")


def _parse_from_string(xml_str: str):
  fd, path = tempfile.mkstemp(suffix=".xml")
  try:
    with os.fdopen(fd, 'w', encoding='utf-8') as f:
      f.write(xml_str)
    return parse_nfe_xml(path)
  finally:
    try:
      os.remove(path)
    except Exception:
      pass


def test_ipi_formula_with_pipi():
    nfe = _parse_from_string(NFE_XML_WITH_PIPI)
    assert nfe.itens, "Nenhum item parseado do XML com pIPI"
    it = nfe.itens[0]
    # Confirma extração de pIPI e vIPI
    assert round(it.ipi_aliq, 2) == 6.50
    assert round(it.ipi, 2) == 9.10

    # Fórmula: (vUnCom * 2) + ((vProd * ipi_aliq / 100) / quantidade)
    formula = "(vUnCom * 2.0) + ((vProd * ipi_aliq / 100) / quantidade)"
    regra = RegraFornecedorCusto(fornecedor=nfe.emitente or "FORNECEDOR TESTE LTDA", formula=formula, ativo=True)
    item_vars = {
        'vUnCom': it.vUnCom,
        'quantidade': it.quantidade,
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
    }
    resultado = regra.calcular_custo(item_vars)
    # Esperado ~ 4.817645 -> 4.82
    assert round(resultado, 2) == 4.82


def test_ipi_formula_without_pipi_fallback():
    nfe = _parse_from_string(NFE_XML_WITHOUT_PIPI)
    assert nfe.itens, "Nenhum item parseado do XML sem pIPI"
    it = nfe.itens[0]
    # pIPI ausente => ipi_aliq extraído deve ser 0.0
    assert round(it.ipi_aliq, 2) == 0.00
    # vIPI presente
    assert round(it.ipi, 2) == 9.10

    # A regra deve calcular ipi_aliq via fallback (ipi_total/vProd * 100)
    formula = "(vUnCom * 2.0) + ((vProd * ipi_aliq / 100) / quantidade)"
    regra = RegraFornecedorCusto(fornecedor=nfe.emitente or "FORNECEDOR TESTE LTDA", formula=formula, ativo=True)
    item_vars = {
        'vUnCom': it.vUnCom,
        'quantidade': it.quantidade,
        'vProd': it.vProd,
        'ipi_total': it.ipi,
        # ipi_aliq omitido/zerado no dict é tratado no fallback interno
        'ipi_aliq': it.ipi_aliq,
        'st_total': it.st,
        'icms_total': it.icms,
        'pis_total': it.pis,
        'cofins_total': it.cofins,
        'rateio_frete': it.rateio_frete,
        'rateio_seguro': it.rateio_seguro,
        'rateio_outros': it.rateio_outros,
        'rateio_desconto': it.rateio_desconto,
    }
    resultado = regra.calcular_custo(item_vars)
    assert round(resultado, 2) == 4.82
