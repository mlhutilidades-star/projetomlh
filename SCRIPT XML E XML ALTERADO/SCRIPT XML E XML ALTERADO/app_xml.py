# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
Gerador de NF-e XML a partir de XML existente
Le arquivo XML, extrai produtos e gera novo XML
Compativel com Tiny: ICMS 20%, FCP 2%, IPI 0%
Salva como .xml pronto para importacao
"""

import json
import os
import sys
import xml.dom.minidom as minidom
import xml.etree.ElementTree as ET
from datetime import datetime

class GeradorNFeFromXML:
    def __init__(self):
        self.arquivo_config = "nfe_config.json"
        self.carregar_config()

    def carregar_config(self):
        if os.path.exists(self.arquivo_config):
            with open(self.arquivo_config, 'r', encoding='utf-8') as f:
                self.config = json.load(f)
        else:
            self.config = self.config_padrao()
            self.salvar_config()

    def config_padrao(self):
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
                    "fone": "021982643677"
                },
                "IE": "15754834",
                "email": "mlhutilidades@gmail.com; mlhutilidadesfinanceiro@gmail.com;"
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
                "pICMS": 20.00,
                "pFCP": 2.00,
                "pIPI": 0.00
            },
            "opcoes": {
                "multiplicar_preco": False,
                "multiplicador": 2.0
            }
        }

    def salvar_config(self):
        with open(self.arquivo_config, 'w', encoding='utf-8') as f:
            json.dump(self.config, f, indent=2, ensure_ascii=False)

    def extrair_produtos_xml(self, arquivo_xml):
        """Extrai produtos de um arquivo XML NF-e"""
        try:
            tree = ET.parse(arquivo_xml)
            root = tree.getroot()
            
            namespaces = {
                'nfe': 'http://www.portalfiscal.inf.br/nfe',
                '': 'http://www.portalfiscal.inf.br/nfe'
            }
            
            produtos = []
            
            for det in root.findall('.//nfe:det', namespaces):
                try:
                    prod = det.find('.//nfe:prod', namespaces)
                    if prod is None:
                        prod = det.find('.//prod')
                    
                    if prod is None:
                        continue
                    
                    def get_text(element, tag):
                        el = element.find('.//{*}' + tag) if element.find('.//{*}' + tag) is not None else element.find(tag)
                        return el.text if el is not None and el.text else "0"
                    
                    cProd = get_text(prod, 'cProd')
                    cEAN = get_text(prod, 'cEAN')
                    xProd = get_text(prod, 'xProd')
                    NCM = get_text(prod, 'NCM')
                    qCom = float(get_text(prod, 'qCom'))
                    vUnCom = float(get_text(prod, 'vUnCom'))
                    
                    CFOP_elem = det.find('.//{*}CFOP')
                    if CFOP_elem is None:
                        CFOP_elem = prod.find('{*}CFOP')
                    CFOP = CFOP_elem.text if CFOP_elem is not None and CFOP_elem.text else "5102"
                    
                    produtos.append({
                        "cProd": cProd if cProd else "PROD" + str(len(produtos) + 1),
                        "cEAN": cEAN if cEAN else "0000000000000",
                        "xProd": xProd if xProd else "PRODUTO",
                        "NCM": NCM if NCM else "95030099",
                        "qCom": int(qCom),
                        "vUnCom": vUnCom,
                        "CFOP": CFOP
                    })
                except (ValueError, AttributeError) as e:
                    print("Aviso: Erro ao processar produto: {}".format(e))
                    continue
            
            return produtos
        except Exception as e:
            print("Erro ao ler XML: {}".format(e))
            return []

    def processar_produtos(self, produtos):
        """Processa produtos (multiplica precos se necessario)"""
        multiplicador = self.config["opcoes"]["multiplicador"] if self.config["opcoes"]["multiplicar_preco"] else 1.0
        vProd_total = 0.0
        for prod in produtos:
            prod["vUnCom"] = round(prod["vUnCom"] * multiplicador, 10)
            prod["vProd"] = round(prod["qCom"] * prod["vUnCom"], 2)
            vProd_total += prod["vProd"]
        return produtos, round(vProd_total, 2)

    def gerar_xml(self, produtos):
        """Gera XML da NF-e"""
        produtos, vProd_total = self.processar_produtos(produtos)

        vBC = vProd_total
        pICMS = self.config["impostos"]["pICMS"]
        pFCP = self.config["impostos"]["pFCP"]
        pIPI = self.config["impostos"]["pIPI"]

        vICMS = round(vBC * (pICMS / 100), 2)
        vFCP = round(vBC * (pFCP / 100), 2)
        vIPI = round(vBC * (pIPI / 100), 2)
        vNF = vBC

        emit = self.config["emit"]
        dest = self.config["dest"]
        ide = self.config["ide"]
        transp = self.config["transp"]
        pag = self.config["pag"]
        infAdic = self.config["infAdic"]
        infRespTec = self.config["infRespTec"]

        xml = """<?xml version="1.0" encoding="UTF-8"?>
<nfeProc xmlns="http://www.portalfiscal.inf.br/nfe" versao="4.00">
<NFe xmlns="http://www.portalfiscal.inf.br/nfe">
<infNFe Id="NFe33251112124596000110550010000336791895875396" versao="4.00">
<ide>
<cUF>{}</cUF>
<cNF>{}</cNF>
<natOp>{}</natOp>
<mod>{}</mod>
<serie>{}</serie>
<nNF>{}</nNF>
<dhEmi>2025-11-13T13:48:00-03:00</dhEmi>
<dhSaiEnt>2025-11-13T13:48:00-03:00</dhSaiEnt>
<tpNF>{}</tpNF>
<idDest>{}</idDest>
<cMunFG>{}</cMunFG>
<tpImp>{}</tpImp>
<tpEmis>{}</tpEmis>
<cDV>{}</cDV>
<tpAmb>{}</tpAmb>
<finNFe>{}</finNFe>
<indFinal>{}</indFinal>
<indPres>{}</indPres>
<indIntermed>{}</indIntermed>
<procEmi>{}</procEmi>
<verProc>{}</verProc>
</ide>
<emit>
<CNPJ>{}</CNPJ>
<xNome>{}</xNome>
<xFant>{}</xFant>
<enderEmit>
<xLgr>{}</xLgr>
<nro>{}</nro>
<xCpl>{}</xCpl>
<xBairro>{}</xBairro>
<cMun>{}</cMun>
<xMun>{}</xMun>
<UF>{}</UF>
<CEP>{}</CEP>
<cPais>1058</cPais>
<xPais>BRASIL</xPais>
<fone>{}</fone>
</enderEmit>
<IE>{}</IE>
<IM>{}</IM>
<CNAE>{}</CNAE>
<CRT>{}</CRT>
</emit>
<dest>
<CNPJ>{}</CNPJ>
<xNome>{}</xNome>
<enderDest>
<xLgr>{}</xLgr>
<nro>{}</nro>
<xBairro>{}</xBairro>
<cMun>{}</cMun>
<xMun>{}</xMun>
<UF>{}</UF>
<CEP>{}</CEP>
<cPais>1058</cPais>
<xPais>BRASIL</xPais>
<fone>{}</fone>
</enderDest>
<indIEDest>1</indIEDest>
<IE>{}</IE>
<email>{}</email>
</dest>
""".format(
            ide['cUF'], ide['cNF'], ide['natOp'], ide['mod'], ide['serie'], ide['nNF'],
            ide['tpNF'], ide['idDest'], ide['cMunFG'], ide['tpImp'], ide['tpEmis'], ide['cDV'],
            ide['tpAmb'], ide['finNFe'], ide['indFinal'], ide['indPres'], ide['indIntermed'],
            ide['procEmi'], ide['verProc'],
            emit['CNPJ'], emit['xNome'], emit['xFant'],
            emit['enderEmit']['xLgr'], emit['enderEmit']['nro'], emit['enderEmit']['xCpl'],
            emit['enderEmit']['xBairro'], emit['enderEmit']['cMun'], emit['enderEmit']['xMun'],
            emit['enderEmit']['UF'], emit['enderEmit']['CEP'], emit['enderEmit']['fone'],
            emit['IE'], emit['IM'], emit['CNAE'], emit['CRT'],
            dest['CNPJ'], dest['xNome'],
            dest['enderDest']['xLgr'], dest['enderDest']['nro'], dest['enderDest']['xBairro'],
            dest['enderDest']['cMun'], dest['enderDest']['xMun'], dest['enderDest']['UF'],
            dest['enderDest']['CEP'], dest['enderDest']['fone'],
            dest['IE'], dest['email']
        )

        nItem = 1
        for prod in produtos:
            vICMS_item = round(prod["vProd"] * (pICMS / 100), 2)
            vFCP_item = round(prod["vProd"] * (pFCP / 100), 2)

            xml += """<det nItem="{}">
<prod>
<cProd>{}</cProd>
<cEAN>{}</cEAN>
<xProd>{}</xProd>
<NCM>{}</NCM>
<cBenef/>
<CFOP>{}</CFOP>
<uCom>PC</uCom>
<qCom>{}.0000</qCom>
<vUnCom>{:.10f}</vUnCom>
<vProd>{:.2f}</vProd>
<cEANTrib>{}</cEANTrib>
<uTrib>PC</uTrib>
<qTrib>{}.0000</qTrib>
<vUnTrib>{:.10f}</vUnTrib>
<indTot>1</indTot>
</prod>
<imposto>
<ICMS>
<ICMS00>
<orig>1</orig>
<CST>00</CST>
<modBC>3</modBC>
<vBC>{:.2f}</vBC>
<pICMS>{:.4f}</pICMS>
<vICMS>{:.2f}</vICMS>
<pFCP>{:.4f}</pFCP>
<vFCP>{:.2f}</vFCP>
</ICMS00>
</ICMS>
<IPI>
<cEnq>999</cEnq>
<IPITrib>
<CST>99</CST>
<vBC>0.00</vBC>
<pIPI>0.00</pIPI>
<vIPI>0.00</vIPI>
</IPITrib>
</IPI>
<PIS>
<PISAliq>
<CST>01</CST>
<vBC>0</vBC>
<pPIS>0</pPIS>
<vPIS>0</vPIS>
</PISAliq>
</PIS>
<COFINS>
<COFINSAliq>
<CST>01</CST>
<vBC>0</vBC>
<pCOFINS>0</pCOFINS>
<vCOFINS>0</vCOFINS>
</COFINSAliq>
</COFINS>
</imposto>
<infAdProd>(FCP): Base R$ {:.2f} Perc.(2%) Vlr. R$ {:.2f}</infAdProd>
</det>
""".format(
                nItem, prod['cProd'], prod['cEAN'], prod['xProd'], prod['NCM'], prod['CFOP'],
                prod['qCom'], prod['vUnCom'], prod['vProd'], prod['cEAN'],
                prod['qCom'], prod['vUnCom'],
                prod['vProd'], pICMS, vICMS_item, pFCP, vFCP_item,
                prod['vProd'], vFCP_item
            )
            nItem += 1

        xml += """<total>
<ICMSTot>
<vBC>{:.2f}</vBC>
<vICMS>{:.2f}</vICMS>
<vICMSDeson>0</vICMSDeson>
<vFCPUFDest>0</vFCPUFDest>
<vICMSUFDest>0</vICMSUFDest>
<vICMSUFRemet>0</vICMSUFRemet>
<vFCP>{:.2f}</vFCP>
<vBCST>0</vBCST>
<vST>0</vST>
<vFCPST>0</vFCPST>
<vFCPSTRet>0</vFCPSTRet>
<vProd>{:.2f}</vProd>
<vFrete>0</vFrete>
<vSeg>0</vSeg>
<vDesc>0</vDesc>
<vII>0</vII>
<vIPI>0.00</vIPI>
<vIPIDevol>0</vIPIDevol>
<vPIS>0</vPIS>
<vCOFINS>0</vCOFINS>
<vOutro>0</vOutro>
<vNF>{:.2f}</vNF>
</ICMSTot>
</total>
<transp>
<modFrete>{}</modFrete>
<transporta>
<CNPJ>{}</CNPJ>
<xNome>{}</xNome>
<IE>{}</IE>
<xEnder>{}</xEnder>
<UF>{}</UF>
</transporta>
<vol>
<qVol>{}</qVol>
<esp>{}</esp>
<pesoL>{}</pesoL>
<pesoB>{}</pesoB>
</vol>
</transp>
<pag>
<detPag>
<indPag>{}</indPag>
<tPag>{}</tPag>
<vPag>{:.2f}</vPag>
</detPag>
</pag>
<infAdic>
<infAdFisco>{} - R$ {:.2f} Base R$ {:.2f} Perc.(2%)</infAdFisco>
<infCpl>{}</infCpl>
</infAdic>
<infRespTec>
<CNPJ>{}</CNPJ>
<xContato>{}</xContato>
<email>{}</email>
<fone>{}</fone>
</infRespTec>
</infNFe>
</NFe>
</nfeProc>
""".format(
            vBC, vICMS, vFCP, vBC, vNF,
            transp['modFrete'], transp['transporta']['CNPJ'], transp['transporta']['xNome'],
            transp['transporta']['IE'], transp['transporta']['xEnder'], transp['transporta']['UF'],
            transp['vol']['qVol'], transp['vol']['esp'], transp['vol']['pesoL'], transp['vol']['pesoB'],
            pag['indPag'], pag['tPag'], vNF,
            infAdic['infAdFisco'], vFCP, vBC, infAdic['infCpl'],
            infRespTec['CNPJ'], infRespTec['xContato'], infRespTec['email'], infRespTec['fone']
        )

        return xml, vBC, vICMS, vFCP, vIPI

    def salvar_xml(self, xml_content, nome_arquivo="nfe_importacao_processada.xml"):
        """Salva XML em arquivo"""
        try:
            dom = minidom.parseString(xml_content)
            xml_formatado = dom.toprettyxml(indent="  ")
            xml_formatado = "\n".join([line for line in xml_formatado.split("\n") if line.strip()])
            with open(nome_arquivo, 'w', encoding='utf-8') as f:
                f.write(xml_formatado)
            return True, nome_arquivo
        except Exception as e:
            return False, str(e)

def main():
    print("=" * 70)
    print("  GERADOR DE NF-e XML A PARTIR DE ARQUIVO XML")
    print("=" * 70)
    print()
    
    gerador = GeradorNFeFromXML()
    
    print("Digite o nome do arquivo XML de entrada:")
    print("(Ex: nfe.xml, documento-nfe.xml)")
    arquivo_xml = input(">> ").strip()
    
    if not arquivo_xml:
        arquivo_xml = "nfe.xml"
    
    if not os.path.exists(arquivo_xml):
        print()
        print("ERRO: Arquivo '{}' nao encontrado!".format(arquivo_xml))
        print()
        print("Arquivos XML disponíveis nesta pasta:")
        xml_files = [f for f in os.listdir('.') if f.endswith('.xml')]
        if xml_files:
            for f in xml_files:
                print("  - {}".format(f))
        else:
            print("  Nenhum arquivo XML encontrado")
        print()
        input("Pressione ENTER para sair...")
        return
    
    print()
    print("Lendo arquivo XML: {}".format(arquivo_xml))
    produtos = gerador.extrair_produtos_xml(arquivo_xml)
    
    if not produtos:
        print("ERRO: Nenhum produto foi extraído do XML!")
        print("Verifique se o arquivo tem o formato correto.")
        input("Pressione ENTER para sair...")
        return
    
    print("Sucesso! {} produto(s) extraído(s)".format(len(produtos)))
    print()
    print("Produtos encontrados:")
    for i, p in enumerate(produtos, 1):
        print("  {}. {} - Qtd: {} - R$ {:.2f}".format(
            i, p['xProd'], p['qCom'], p['vUnCom']
        ))
    print()
    
    print("OPCOES DE PROCESSAMENTO:")
    print("1 - Gerar XML com precos ORIGINAIS")
    print("2 - Gerar XML com precos MULTIPLICADOS por 2")
    opcao = input("Escolha (1 ou 2): ").strip()
    
    if opcao == "2":
        gerador.config["opcoes"]["multiplicar_preco"] = True
        print("Precos serao multiplicados por 2.")
    else:
        gerador.config["opcoes"]["multiplicar_preco"] = False
        print("Usando precos originais.")
    
    print()
    print("Gerando novo XML...")
    xml_content, vProd, vICMS, vFCP, vIPI = gerador.gerar_xml(produtos)
    sucesso, caminho = gerador.salvar_xml(xml_content)
    
    print()
    if sucesso:
        print("=" * 70)
        print("XML GERADO COM SUCESSO!")
        print("=" * 70)
        print()
        print("Arquivo salvo: {}".format(caminho))
        print()
        print("RESUMO:")
        print("  Produtos: {}".format(len(produtos)))
        print("  Total Produtos: R$ {:.2f}".format(vProd))
        print("  ICMS (20%%): R$ {:.2f}".format(vICMS))
        print("  FCP (2%%): R$ {:.2f}".format(vFCP))
        print("  IPI: R$ {:.2f} (zerado)".format(vIPI))
        print("  TOTAL NF: R$ {:.2f}".format(vProd))
        print()
        print("Pronto para importar no Tiny!")
        print("=" * 70)
    else:
        print("ERRO ao salvar XML: {}".format(caminho))

    print()
    input("Pressione ENTER para sair...")

if __name__ == "__main__":
    main()