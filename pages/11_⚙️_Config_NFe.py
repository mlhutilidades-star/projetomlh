"""
Configuração de dados para geração de NF-e completa.
Permite customizar emitente, destinatário, impostos, etc.
"""
import streamlit as st
import copy
import json
import os
from pathlib import Path

from modules.nfe_generator import _config_padrao as generator_config_padrao

# Arquivo de configuração
CONFIG_FILE = Path("data/nfe_config.json")

st.set_page_config(
    page_title="Configuração NF-e",
    page_icon="⚙️",
    layout="wide"
)

st.title("⚙️ Configuração de Geração de NF-e")
st.markdown("Configure os dados usados para gerar XMLs completos compatíveis com Tiny")

st.error("""
⚠️ **IMPORTANTE**: O Tiny NÃO aceita CNPJ zerado (00000000000000)!

Configure os CNPJs corretos abaixo, caso contrário receberá **erro 35** ao enviar.
""")

def _merge_dict(base: dict, override: dict) -> dict:
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(base.get(key), dict):
            _merge_dict(base[key], value)
        else:
            base[key] = value
    return base

def carregar_config():
    """Carrega configuração mesclando com padrão para garantir novos campos"""
    cfg = config_padrao()
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            try:
                stored = json.load(f)
                cfg = _merge_dict(cfg, stored)
            except json.JSONDecodeError:
                st.warning("Arquivo de configuração inválido. Restaurando padrão.")
    return cfg

def salvar_config(config):
    """Salva configuração em arquivo"""
    CONFIG_FILE.parent.mkdir(exist_ok=True)
    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2, ensure_ascii=False)

def config_padrao():
    """Obtém cópia da configuração padrão do gerador"""
    return copy.deepcopy(generator_config_padrao())

# Carregar configuração
config = carregar_config()

# Garantir estrutura mínima
config.setdefault("emit", {}).setdefault("enderEmit", {})
config.setdefault("dest", {}).setdefault("enderDest", {})
config.setdefault("impostos", {})
config.setdefault("ide", {})
config.setdefault("transp", {}).setdefault("transporta", {})
config["transp"].setdefault("vol", {})
config.setdefault("pag", {})
config.setdefault("infAdic", {})
config.setdefault("infRespTec", {})

st.markdown("---")

# Abas para diferentes seções
tab1, tab2, tab3, tab4 = st.tabs(["🏢 Emitente", "👤 Destinatário", "💰 Impostos", "📋 Outras Info"])

with tab1:
    st.subheader("🏢 Dados do Emitente")
    st.caption("Empresa que está emitindo a NF-e")
    
    col1, col2 = st.columns(2)
    with col1:
        config["emit"]["CNPJ"] = st.text_input("CNPJ", config["emit"]["CNPJ"])
        config["emit"]["xNome"] = st.text_input("Razão Social", config["emit"]["xNome"])
        config["emit"]["xFant"] = st.text_input("Nome Fantasia", config["emit"]["xFant"])
        config["emit"]["IE"] = st.text_input("Inscrição Estadual", config["emit"]["IE"])
        config["emit"]["CRT"] = st.selectbox(
            "Regime Tributário (CRT)",
            options=["1", "2", "3"],
            index=["1", "2", "3"].index(config["emit"]["CRT"]),
            format_func=lambda x: {
                "1": "1 - Simples Nacional",
                "2": "2 - Simples Nacional - Excesso",
                "3": "3 - Regime Normal"
            }[x]
        )
    
    with col2:
        st.markdown("**Endereço**")
        config["emit"]["enderEmit"]["xLgr"] = st.text_input("Logradouro", config["emit"]["enderEmit"]["xLgr"])
        config["emit"]["enderEmit"]["nro"] = st.text_input("Número", config["emit"]["enderEmit"]["nro"])
        config["emit"]["enderEmit"]["xCpl"] = st.text_input("Complemento", config["emit"]["enderEmit"]["xCpl"])
        config["emit"]["enderEmit"]["xBairro"] = st.text_input("Bairro", config["emit"]["enderEmit"]["xBairro"])
        
        col_uf, col_mun = st.columns(2)
        with col_uf:
            config["emit"]["enderEmit"]["UF"] = st.text_input("UF", config["emit"]["enderEmit"]["UF"])
        with col_mun:
            config["emit"]["enderEmit"]["CEP"] = st.text_input("CEP", config["emit"]["enderEmit"]["CEP"])
        
        config["emit"]["enderEmit"]["xMun"] = st.text_input("Município", config["emit"]["enderEmit"]["xMun"])
        config["emit"]["enderEmit"]["cMun"] = st.text_input("Código IBGE", config["emit"]["enderEmit"]["cMun"])
        config["emit"]["enderEmit"]["cPais"] = st.text_input("Código País", config["emit"]["enderEmit"].get("cPais", "1058"))
        config["emit"]["enderEmit"]["xPais"] = st.text_input("País", config["emit"]["enderEmit"].get("xPais", "BRASIL"))
        config["emit"]["enderEmit"]["fone"] = st.text_input("Telefone", config["emit"]["enderEmit"].get("fone", ""))

with tab2:
    st.subheader("👤 Dados do Destinatário Padrão")
    st.caption("Usado quando gerar XML completo (pode ser diferente da nota original)")
    
    col1, col2 = st.columns(2)
    with col1:
        config["dest"]["CNPJ"] = st.text_input("CNPJ Destinatário", config["dest"]["CNPJ"])
        config["dest"]["xNome"] = st.text_input("Razão Social Destinatário", config["dest"]["xNome"])
        config["dest"]["IE"] = st.text_input("IE Destinatário", config["dest"]["IE"])
        config["dest"]["email"] = st.text_input("Email", config["dest"]["email"])
    
    with col2:
        st.markdown("**Endereço**")
        config["dest"]["enderDest"]["xLgr"] = st.text_input("Logradouro Dest", config["dest"]["enderDest"]["xLgr"], key="dest_lgr")
        config["dest"]["enderDest"]["nro"] = st.text_input("Número Dest", config["dest"]["enderDest"]["nro"], key="dest_nro")
        config["dest"]["enderDest"]["xBairro"] = st.text_input("Bairro Dest", config["dest"]["enderDest"]["xBairro"], key="dest_bairro")
        
        col_uf2, col_cep2 = st.columns(2)
        with col_uf2:
            config["dest"]["enderDest"]["UF"] = st.text_input("UF Dest", config["dest"]["enderDest"]["UF"], key="dest_uf")
        with col_cep2:
            config["dest"]["enderDest"]["CEP"] = st.text_input("CEP Dest", config["dest"]["enderDest"]["CEP"], key="dest_cep")
        
        config["dest"]["enderDest"]["xMun"] = st.text_input("Município Dest", config["dest"]["enderDest"]["xMun"], key="dest_mun")
        config["dest"]["enderDest"]["cMun"] = st.text_input("Código IBGE Dest", config["dest"]["enderDest"]["cMun"], key="dest_cmun")
        config["dest"]["enderDest"]["cPais"] = st.text_input("Código País Dest", config["dest"]["enderDest"].get("cPais", "1058"), key="dest_cpais")
        config["dest"]["enderDest"]["xPais"] = st.text_input("País Dest", config["dest"]["enderDest"].get("xPais", "BRASIL"), key="dest_xpais")
        config["dest"]["enderDest"]["fone"] = st.text_input("Telefone Dest", config["dest"]["enderDest"].get("fone", ""), key="dest_fone")

with tab3:
    st.subheader("💰 Alíquotas de Impostos")
    st.caption("Valores padrão usados na geração de XML completo")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        config["impostos"]["pICMS"] = st.number_input(
            "ICMS (%)",
            min_value=0.0,
            max_value=100.0,
            value=config["impostos"]["pICMS"],
            step=0.01,
            help="Alíquota de ICMS. Ex: 20.00"
        )
    
    with col2:
        config["impostos"]["pFCP"] = st.number_input(
            "FCP (%)",
            min_value=0.0,
            max_value=100.0,
            value=config["impostos"]["pFCP"],
            step=0.01,
            help="Fundo de Combate à Pobreza. Ex: 2.00"
        )
    
    with col3:
        config["impostos"]["pIPI"] = st.number_input(
            "IPI (%)",
            min_value=0.0,
            max_value=100.0,
            value=config["impostos"]["pIPI"],
            step=0.01,
            help="Imposto sobre Produtos Industrializados. Ex: 0.00"
        )
    
    st.info("""
    ℹ️ **Sobre os impostos:**
    - **ICMS**: Destacado mas NÃO somado ao total da nota
    - **FCP**: Adicional de alíquota do fundo estadual
    - **IPI**: Normalmente 0% para revenda
    """)

with tab4:
    st.subheader("📋 Outras Informações e Avançado")
    st.caption("Configure todos os campos da seção IDE e blocos auxiliares (transporte, pagamento, informações adicionais e responsável técnico).")

    ide = config["ide"]

    def select_with_default(label, options, current, help_text=None, format_func=None, key=None):
        value = current if current in options else options[0]
        idx = options.index(value)
        return st.selectbox(label, options=options, index=idx, help=help_text, format_func=format_func, key=key)

    st.markdown("#### 🧾 Identificação (IDE)")
    col_a, col_b, col_c = st.columns(3)
    with col_a:
        ide["natOp"] = st.text_input("Natureza da Operação", ide.get("natOp", "VENDA"))
        ide["serie"] = st.text_input("Série", ide.get("serie", "1"))
    with col_b:
        ide["nNF"] = st.text_input("Número da NF (nNF)", ide.get("nNF", ""))
        ide["cNF"] = st.text_input("Código Numérico (cNF)", ide.get("cNF", ""))
    with col_c:
        ide["cUF"] = st.text_input("Código UF", ide.get("cUF", "33"), help="Código IBGE do estado emitente")
        ide["cMunFG"] = st.text_input("Município de Ocorrência (cMunFG)", ide.get("cMunFG", ""))

    col_d, col_e, col_f = st.columns(3)
    with col_d:
        ide["tpNF"] = select_with_default(
            "Tipo de Nota (tpNF)",
            ["0", "1"],
            ide.get("tpNF", "1"),
            format_func=lambda x: "0 - Entrada" if x == "0" else "1 - Saída"
        )
        ide["idDest"] = select_with_default(
            "Destino da Operação (idDest)",
            ["1", "2", "3"],
            ide.get("idDest", "1"),
            format_func=lambda x: {
                "1": "1 - Interna",
                "2": "2 - Interestadual",
                "3": "3 - Exterior"
            }[x]
        )
    with col_e:
        ide["tpImp"] = select_with_default(
            "Formato DANFE (tpImp)", ["0", "1", "2", "3", "4"], ide.get("tpImp", "1"),
            format_func=lambda x: {
                "0": "0 - Sem DANFE",
                "1": "1 - Retrato",
                "2": "2 - Paisagem",
                "3": "3 - Simplificado",
                "4": "4 - NFC-e"
            }.get(x, x)
        )
        ide["tpEmis"] = select_with_default(
            "Tipo de Emissão (tpEmis)", ["1", "2", "3", "4", "5", "6", "7", "8"], ide.get("tpEmis", "1")
        )
    with col_f:
        ide["tpAmb"] = select_with_default(
            "Ambiente (tpAmb)", ["1", "2"], ide.get("tpAmb", "1"),
            format_func=lambda x: "1 - Produção" if x == "1" else "2 - Homologação"
        )
        ide["cDV"] = st.text_input("Dígito Verificador (cDV)", ide.get("cDV", ""))

    col_g, col_h, col_i = st.columns(3)
    with col_g:
        ide["finNFe"] = select_with_default(
            "Finalidade (finNFe)", ["1", "2", "3", "4"], ide.get("finNFe", "1"),
            format_func=lambda x: {
                "1": "1 - Normal",
                "2": "2 - Complementar",
                "3": "3 - Ajuste",
                "4": "4 - Devolução"
            }[x]
        )
    with col_h:
        ide["indFinal"] = select_with_default(
            "Consumidor Final (indFinal)", ["0", "1"], ide.get("indFinal", "0"),
            format_func=lambda x: "0 - Normal" if x == "0" else "1 - Consumidor"
        )
    with col_i:
        ide["indPres"] = select_with_default(
            "Indicador de Presença (indPres)",
            ["0", "1", "2", "3", "4", "5", "9"],
            ide.get("indPres", "9")
        )

    col_j, col_k, col_l = st.columns(3)
    with col_j:
        ide["indIntermed"] = select_with_default("Intermediador (indIntermed)", ["0", "1", "2"], ide.get("indIntermed", "0"))
    with col_k:
        ide["procEmi"] = select_with_default("Processo de Emissão (procEmi)", ["0", "1", "2", "3"], ide.get("procEmi", "0"))
    with col_l:
        ide["verProc"] = st.text_input("Versão do Processo (verProc)", ide.get("verProc", ""))

    st.divider()

    with st.expander("🚚 Transporte e Volume", expanded=False):
        transp = config["transp"]
        transp["modFrete"] = select_with_default(
            "Modalidade de Frete (modFrete)", ["0", "1", "2", "3", "4", "9"], transp.get("modFrete", "0"),
            format_func=lambda x: {
                "0": "0 - Emitente",
                "1": "1 - Destinatário",
                "2": "2 - Terceiros",
                "3": "3 - Próprio Remetente",
                "4": "4 - Próprio Destinatário",
                "9": "9 - Sem Transporte"
            }.get(x, x)
        )
        transporta = transp.setdefault("transporta", {})
        col_t1, col_t2 = st.columns(2)
        with col_t1:
            transporta["CNPJ"] = st.text_input("CNPJ Transportadora", transporta.get("CNPJ", ""))
            transporta["xNome"] = st.text_input("Nome Transportadora", transporta.get("xNome", ""))
        with col_t2:
            transporta["IE"] = st.text_input("IE Transportadora", transporta.get("IE", ""))
            transporta["UF"] = st.text_input("UF Transportadora", transporta.get("UF", ""))
        transporta["xEnder"] = st.text_input("Endereço Transportadora", transporta.get("xEnder", ""))

        vol = transp.setdefault("vol", {})
        col_v1, col_v2, col_v3 = st.columns(3)
        with col_v1:
            vol["qVol"] = st.text_input("Quantidade Volumes", vol.get("qVol", ""))
        with col_v2:
            vol["esp"] = st.text_input("Espécie", vol.get("esp", ""))
        with col_v3:
            vol["pesoL"] = st.text_input("Peso Líquido", vol.get("pesoL", ""))
        vol["pesoB"] = st.text_input("Peso Bruto", vol.get("pesoB", ""))

    with st.expander("💳 Pagamento", expanded=False):
        pag = config["pag"]
        pag["indPag"] = select_with_default(
            "Indicador Pagamento (indPag)", ["0", "1", "2"], pag.get("indPag", "0"),
            format_func=lambda x: {
                "0": "0 - Pagamento à vista",
                "1": "1 - A prazo",
                "2": "2 - Outros"
            }[x]
        )
        pag["tPag"] = select_with_default(
            "Forma de Pagamento (tPag)",
            ["01", "02", "03", "04", "05", "10", "11", "12", "13", "14", "15", "16", "90", "99"],
            pag.get("tPag", "16"),
            help_text="Código tPag conforme NT 2015/002"
        )

    with st.expander("📝 Informações Adicionais", expanded=False):
        inf_adic = config["infAdic"]
        inf_adic["infAdFisco"] = st.text_input("Mensagem ao Fisco", inf_adic.get("infAdFisco", ""))
        inf_adic["infCpl"] = st.text_area("Informações Complementares", inf_adic.get("infCpl", ""), height=120)

    with st.expander("👨‍💻 Responsável Técnico", expanded=False):
        resp = config["infRespTec"]
        resp["CNPJ"] = st.text_input("CNPJ Responsável", resp.get("CNPJ", ""))
        resp["xContato"] = st.text_input("Contato", resp.get("xContato", ""))
        resp["email"] = st.text_input("Email Técnico", resp.get("email", ""))
        resp["fone"] = st.text_input("Telefone Técnico", resp.get("fone", ""))

st.markdown("---")

# Botões de ação
col1, col2, col3 = st.columns([1, 1, 4])

with col1:
    if st.button("💾 Salvar Configuração", type="primary"):
        salvar_config(config)
        st.success("✅ Configuração salva com sucesso!")
        st.rerun()

with col2:
    if st.button("🔄 Restaurar Padrão"):
        config = config_padrao()
        salvar_config(config)
        st.warning("⚠️ Configuração restaurada para valores padrão")
        st.rerun()

# Preview JSON
with st.expander("🔍 Ver JSON Completo"):
    st.json(config)

st.markdown("---")
st.caption("💡 Esta configuração é usada apenas no modo **'Gerar XML Completo'** da página Upload PDF")
