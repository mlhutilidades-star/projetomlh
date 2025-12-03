"""
Testes para o módulo de modificação de XML NF-e (modules/nfe_modifier.py)
"""
import pytest
from modules.nfe_modifier import modificar_xml_nfe_com_custos


class TestNfeModifier:
    """Tests for NFe XML modification"""
    
    def test_modificar_xml_com_custos_basic(self):
        """Test basic XML modification with cost replacement"""
        xml_input = '''<?xml version="1.0" encoding="UTF-8"?>
<nfeProc xmlns="http://www.portalfiscal.inf.br/nfe">
    <NFe>
        <infNFe>
            <det nItem="1">
                <prod>
                    <cProd>PROD001</cProd>
                    <qCom>2.0000</qCom>
                    <vUnCom>100.0000</vUnCom>
                    <vProd>200.00</vProd>
                    <vUnTrib>100.0000</vUnTrib>
                </prod>
            </det>
        </infNFe>
    </NFe>
</nfeProc>'''
        
        custos = {"PROD001": 75.50}
        
        result = modificar_xml_nfe_com_custos(xml_input, custos)
        
        # Verify XML declaration preserved
        assert '<?xml version="1.0" encoding="UTF-8"?>' in result
        
        # Verify cost replaced
        assert '75.5000' in result
        
        # Verify vProd recalculated (2.0 * 75.5 = 151.0)
        assert '151.00' in result
    
    def test_modificar_xml_multiple_items(self):
        """Test XML modification with multiple items"""
        xml_input = '''<?xml version="1.0" encoding="UTF-8"?>
<nfeProc xmlns="http://www.portalfiscal.inf.br/nfe">
    <NFe>
        <infNFe>
            <det nItem="1">
                <prod>
                    <cProd>PROD001</cProd>
                    <qCom>2.0000</qCom>
                    <vUnCom>100.0000</vUnCom>
                    <vProd>200.00</vProd>
                </prod>
            </det>
            <det nItem="2">
                <prod>
                    <cProd>PROD002</cProd>
                    <qCom>3.0000</qCom>
                    <vUnCom>50.0000</vUnCom>
                    <vProd>150.00</vProd>
                </prod>
            </det>
        </infNFe>
    </NFe>
</nfeProc>'''
        
        custos = {
            "PROD001": 75.50,
            "PROD002": 40.25
        }
        
        result = modificar_xml_nfe_com_custos(xml_input, custos)
        
        # Verify both costs replaced
        assert '75.5000' in result
        assert '40.2500' in result
        
        # Verify vProd recalculated
        assert '151.00' in result  # 2 * 75.5
        assert '120.75' in result  # 3 * 40.25
    
    def test_modificar_xml_missing_sku(self):
        """Test XML modification when SKU not in cost dict"""
        xml_input = '''<?xml version="1.0" encoding="UTF-8"?>
<nfeProc xmlns="http://www.portalfiscal.inf.br/nfe">
    <NFe>
        <infNFe>
            <det nItem="1">
                <prod>
                    <cProd>PROD001</cProd>
                    <qCom>2.0000</qCom>
                    <vUnCom>100.0000</vUnCom>
                    <vProd>200.00</vProd>
                </prod>
            </det>
            <det nItem="2">
                <prod>
                    <cProd>PROD999</cProd>
                    <qCom>1.0000</qCom>
                    <vUnCom>50.0000</vUnCom>
                    <vProd>50.00</vProd>
                </prod>
            </det>
        </infNFe>
    </NFe>
</nfeProc>'''
        
        custos = {"PROD001": 75.50}  # PROD999 not in dict
        
        result = modificar_xml_nfe_com_custos(xml_input, custos)
        
        # PROD001 should be modified
        assert '75.5000' in result
        
        # PROD999 should remain unchanged
        assert '50.0000' in result
    
    def test_modificar_xml_preserves_structure(self):
        """Test that XML structure is preserved"""
        xml_input = '''<?xml version="1.0" encoding="UTF-8"?>
<nfeProc xmlns="http://www.portalfiscal.inf.br/nfe">
    <NFe>
        <infNFe>
            <det nItem="1">
                <prod>
                    <cProd>PROD001</cProd>
                    <xProd>Product Name</xProd>
                    <qCom>1.0000</qCom>
                    <vUnCom>100.0000</vUnCom>
                    <vProd>100.00</vProd>
                </prod>
            </det>
        </infNFe>
    </NFe>
</nfeProc>'''
        
        custos = {"PROD001": 90.00}
        
        result = modificar_xml_nfe_com_custos(xml_input, custos)
        
        # Verify structure preserved (ElementTree adds ns0 prefix)
        assert 'nfeProc' in result
        assert 'PROD001' in result
        assert 'Product Name' in result
        assert '90.0000' in result  # Cost changed
        assert '90.00' in result  # vProd recalculated
    
    def test_modificar_xml_empty_custos(self):
        """Test XML modification with empty cost dictionary"""
        xml_input = '''<?xml version="1.0" encoding="UTF-8"?>
<nfeProc xmlns="http://www.portalfiscal.inf.br/nfe">
    <NFe>
        <infNFe>
            <det nItem="1">
                <prod>
                    <cProd>PROD001</cProd>
                    <qCom>2.0000</qCom>
                    <vUnCom>100.0000</vUnCom>
                    <vProd>200.00</vProd>
                </prod>
            </det>
        </infNFe>
    </NFe>
</nfeProc>'''
        
        custos = {}  # Empty dict
        
        result = modificar_xml_nfe_com_custos(xml_input, custos)
        
        # Original values should remain unchanged
        assert '100.0000' in result
        assert '200.00' in result
