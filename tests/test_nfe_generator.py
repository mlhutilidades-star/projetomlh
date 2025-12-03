import xml.etree.ElementTree as ET
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from modules.nfe_generator import gerar_nfe_completa, _config_padrao
from modules.nfe_parser import NFeDoc, NFeItem


def _sample_nfe():
    item = NFeItem(
        codigo="AKT1000",
        descricao="Produto Teste",
        ncm="95030099",
        cfop="1102",
        quantidade=10.0,
        vUnCom=5.0,
        vProd=50.0,
        ipi=0.0,
        ipi_aliq=0.0,
        st=0.0,
        icms=0.0,
        pis=0.0,
        cofins=0.0,
    )
    return NFeDoc(
        numero="123",
        serie="1",
        chave="12345678901234567890123456789012345678901234",
        emitente="Fornecedor",
        destinatario="Cliente",
        vFrete=0.0,
        vSeguro=0.0,
        vDesc=0.0,
        vOutro=0.0,
        itens=[item],
    )


def _ns():
    return {"nfe": "http://www.portalfiscal.inf.br/nfe"}


def test_xml_envuelve_nfeproc_e_tipo_saida():
    xml = gerar_nfe_completa(_sample_nfe(), {"AKT1000": 7.5})
    root = ET.fromstring(xml.encode("utf-8"))
    assert root.tag.endswith("nfeProc"), "Documento precisa estar dentro de <nfeProc>"
    tp_nf = root.find('.//nfe:tpNF', _ns())
    assert tp_nf is not None and tp_nf.text == '1'


def test_cfop_convertido_para_saida_e_blocos_obrigatorios():
    cfg = _config_padrao()
    xml = gerar_nfe_completa(_sample_nfe(), {"AKT1000": 10.0}, cfg)
    root = ET.fromstring(xml.encode("utf-8"))
    ns = _ns()

    cfop = root.find('.//nfe:CFOP', ns)
    assert cfop is not None
    assert cfop.text.startswith('5') or cfop.text.startswith('6')

    det_pag = root.find('.//nfe:detPag', ns)
    assert det_pag is not None
    ind_pag = det_pag.find('nfe:indPag', ns)
    assert ind_pag is not None and ind_pag.text == cfg['pag']['indPag']

    transporta = root.find('.//nfe:transporta', ns)
    assert transporta is not None

    resp_tecnico = root.find('.//nfe:infRespTec', ns)
    assert resp_tecnico is not None