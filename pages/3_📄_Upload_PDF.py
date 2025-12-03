import streamlit as st
from modules.pdf_parser import extract_from_pdf, ocr_status
from modules import database
from modules.rules import get_rule_for_cnpj
from modules.nfe_parser import parse_nfe_xml, to_rows
from modules.database import get_regra_custo, add_or_update_regra_custo
import tempfile
import os
import logging

logger = logging.getLogger("page_upload_xml")

st.title("📄 Upload de PDF/XML")
st.caption(ocr_status())

tab1, tab2 = st.tabs(["📄 Boleto PDF", "📦 NF-e XML"])

with tab1:
    st.markdown("### Upload de Boleto")
    uploaded = st.file_uploader("Envie um boleto em PDF", type=['pdf'], key="pdf_upload")

    if uploaded:
        pdf_bytes = uploaded.read()
        st.info("Processando arquivo...")
        dados = extract_from_pdf(pdf_bytes, filename=uploaded.name)

        with st.expander("Dados extraídos (preview)"):
            st.json(dados)

        # Prefill regra
        regra = get_rule_for_cnpj(dados.get('cnpj'))
        fornecedor_sug = regra['fornecedor'] if regra else ''
        categoria_sug = regra['categoria'] if regra else ''

        st.markdown("### Confirmar e Salvar")
        with st.form("salvar_pdf"):
            fornecedor = st.text_input("Fornecedor", value=fornecedor_sug)
            categoria = st.text_input("Categoria", value=categoria_sug)
            valor_str = dados.get('valor', '')
            valor = st.text_input("Valor (ex: 120.50)", value=valor_str)
            vencimento = st.text_input("Vencimento (DD/MM/AAAA)", value=dados.get('vencimento', ''))
            cnpj = st.text_input("CNPJ", value=dados.get('cnpj', ''))
            linha = st.text_input("Linha Digitável", value=dados.get('linha_digitavel', ''))
            submit = st.form_submit_button("Salvar Conta")
            if submit:
                try:
                    valor_float = float(valor) if valor else 0.0
                except ValueError:
                    valor_float = 0.0
                database.add_conta({
                    'vencimento': vencimento,
                    'fornecedor': fornecedor,
                    'cnpj': cnpj,
                    'categoria': categoria,
                    'descricao': 'Importado de PDF',
                    'valor': valor_float,
                    'status': 'Pendente',
                    'linha_digitavel': linha,
                    'pdf_path': uploaded.name
                })
                database.add_or_update_regra(cnpj, fornecedor, categoria)
                st.success("Conta salva com dados do PDF!")

with tab2:
    st.markdown("### Upload de NF-e XML")
    st.caption("Faça upload do XML da nota fiscal para extrair dados de produtos e criar regras de custo")
    
    uploaded_xml = st.file_uploader("Envie uma NF-e em XML", type=['xml'], key="xml_upload")
    
    if uploaded_xml:
        # Ler conteúdo do arquivo (importante: usar getvalue() para não esgotar o buffer)
        xml_bytes = uploaded_xml.getvalue()
        
        # Salvar temporariamente para parse
        with tempfile.NamedTemporaryFile(mode='wb', suffix='.xml', delete=False) as tmp:
            tmp.write(xml_bytes)
            tmp_path = tmp.name
        
        try:
            st.info("📦 Processando NF-e...")
            nfe = parse_nfe_xml(tmp_path)
            
            # Campo para ajustar valor de frete (opcional)
            st.markdown("---")
            st.markdown("### 🚚 Ajuste de Frete (Opcional)")
            col_frete1, col_frete2 = st.columns([2, 1])
            with col_frete1:
                frete_xml = nfe.vFrete
                st.caption(f"Frete extraído do XML: R$ {frete_xml:.2f}")
                frete_ajustado = st.number_input(
                    "Valor do Frete para Rateio",
                    min_value=0.0,
                    value=frete_xml,
                    step=0.01,
                    format="%.2f",
                    help="Se o frete for CIF (por conta do fornecedor), deixe em 0. Se FOB, ajuste o valor conforme necessário."
                )
            with col_frete2:
                if frete_ajustado != frete_xml:
                    st.warning(f"⚠️ Alterado de R$ {frete_xml:.2f}")
                elif frete_ajustado == 0:
                    st.info("💡 Frete CIF (sem rateio)")
            
            # Recalcular rateios se frete foi alterado
            if frete_ajustado != frete_xml:
                nfe.vFrete = frete_ajustado
                # Recalcular rateios proporcionais
                soma_vProd = sum(item.vProd for item in nfe.itens)
                for it in nfe.itens:
                    base = it.vProd / soma_vProd if soma_vProd > 0 else 0.0
                    it.rateio_frete = frete_ajustado * base
                    it.rateio_seguro = nfe.vSeguro * base
                    it.rateio_outros = nfe.vOutro * base
                    it.rateio_desconto = nfe.vDesc * base
                    total_rateios = it.rateio_frete + it.rateio_seguro + it.rateio_outros - it.rateio_desconto
                    ipi_unit = (it.ipi / it.quantidade) if it.quantidade else 0.0
                    st_unit = (it.st / it.quantidade) if it.quantidade else 0.0
                    rateio_unit = (total_rateios / it.quantidade) if it.quantidade else 0.0
                    it.custo_sugerido_unit = it.vUnCom + rateio_unit + ipi_unit + st_unit

            st.markdown("---")
            # Mostrar informações da nota
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Número NF-e", nfe.numero)
            with col2:
                st.metric("Série", nfe.serie)
            with col3:
                st.metric("Itens", len(nfe.itens))
            with col4:
                # Mostrar modelo com indicador visual de compatibilidade
                modelo_ok = nfe.modelo == '55'
                st.metric(
                    "Modelo", 
                    nfe.modelo,
                    delta="✅ Compatível" if modelo_ok else "❌ Incompatível",
                    delta_color="normal" if modelo_ok else "inverse"
                )
            
            st.markdown(f"**Fornecedor:** {nfe.emitente}")
            st.markdown(f"**Destinatário:** {nfe.destinatario}")
            
            # Alerta se modelo incompatível
            if nfe.modelo != '55':
                st.error(f"""
                ⚠️ **ATENÇÃO: Nota incompatível com Tiny ERP**
                
                - **Modelo detectado:** {nfe.modelo} ({
                    'NFC-e (Venda ao Consumidor)' if nfe.modelo == '65' else 
                    'CTe (Transporte)' if nfe.modelo == '57' else
                    'NFS-e (Serviço)' if nfe.modelo == '99' else
                    'Outro tipo de documento'
                })
                - **Modelo necessário:** 55 (NF-e de Produtos/Mercadorias)
                
                O Tiny ERP **só aceita NF-e modelo 55** para criar registros de custo via API.
                
                **Você precisa:**
                1. Obter uma NF-e de **entrada de mercadorias** (compra de produtos)
                2. Não usar NFC-e (vendas), CTe (transporte) ou outros tipos
                """)

            # Verificar se já existe regra para este fornecedor
            regra_existente = get_regra_custo(nfe.emitente)

            col_regra1, col_regra2 = st.columns([3, 1])
            with col_regra1:
                if regra_existente:
                    st.success(f"✅ Regra existente encontrada para '{nfe.emitente}'")
                    with st.expander("Ver regra atual"):
                        st.code(regra_existente['formula'])
                        st.caption(f"Usada {regra_existente['contador_usos']} vezes • Última atualização: {regra_existente['ultima_atualizacao']}")
                        if regra_existente['observacoes']:
                            st.caption(f"📝 {regra_existente['observacoes']}")
                else:
                    st.warning(f"⚠️ Nenhuma regra cadastrada para '{nfe.emitente}'")
            
            with col_regra2:
                if regra_existente:
                    if st.button("✏️ Editar Regra", use_container_width=True):
                        st.session_state['editar_regra_xml'] = True
                    if not regra_existente['ativo']:
                        st.warning("⚠️ Regra inativa")
            
            # Preview dos itens
            with st.expander("📋 Ver itens extraídos", expanded=True):
                rows = to_rows(nfe)
                import pandas as pd
                df = pd.DataFrame(rows)
                # Coluna opcional para override manual de SKU (GTIN/EAN)
                # Prefill com o SKU extraído do XML para facilitar a conferência/edição
                if 'sku_override' not in df.columns:
                    df['sku_override'] = df['sku'] if 'sku' in df.columns else None
                # Enriquecer com frete unitário e outros rateios por unidade
                if 'rateio_frete' in df.columns and 'quantidade' in df.columns:
                    df['frete_unit'] = (df['rateio_frete'] / df['quantidade']).fillna(0.0)
                if 'rateio_seguro' in df.columns and 'quantidade' in df.columns:
                    df['seguro_unit'] = (df['rateio_seguro'] / df['quantidade']).fillna(0.0)
                if 'rateio_outros' in df.columns and 'quantidade' in df.columns:
                    df['outros_unit'] = (df['rateio_outros'] / df['quantidade']).fillna(0.0)
                if 'rateio_desconto' in df.columns and 'quantidade' in df.columns:
                    df['desconto_unit'] = (df['rateio_desconto'] / df['quantidade']).fillna(0.0)

                # Pré-visualização: custo calculado por item aplicando a regra atual (se disponível)
                try:
                    from modules.regras_custo import RegraFornecedorCusto
                    regra_para_preview = None
                    # Usa regra existente se ativa; senão tenta usar a fórmula gerada no modo assistido/manual (se já foi definida acima via session_state)
                    if regra_existente and regra_existente.get('ativo') and regra_existente.get('formula'):
                        regra_para_preview = RegraFornecedorCusto(
                            fornecedor=nfe.emitente,
                            formula=regra_existente['formula'],
                            ativo=True
                        )
                    # Caso não exista regra salva, tenta usar uma fórmula temporária da sessão (se usuário gerou uma)
                    elif 'formula_input' in locals() and formula_input:
                        regra_para_preview = RegraFornecedorCusto(
                            fornecedor=nfe.emitente,
                            formula=formula_input,
                            ativo=True
                        )

                    if regra_para_preview is not None:
                        custos_preview = []
                        # Criar mapas: sku extraído do XML + sku_override (manual)
                        overrides = st.session_state.get('itens_overrides_xml', [])
                        map_sku_by_codigo = {str(o.get('codigo')): (o.get('sku') or '') for o in overrides}
                        map_override_by_codigo = {str(o.get('codigo')): (o.get('sku_override') or '') for o in overrides}
                        map_sku_by_desc = {str(o.get('descricao')): (o.get('sku') or '') for o in overrides}
                        map_override_by_desc = {str(o.get('descricao')): (o.get('sku_override') or '') for o in overrides}

                        for it in nfe.itens:
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
                                'rateio_desconto': it.rateio_desconto
                            }
                            try:
                                custo = regra_para_preview.calcular_custo(item_vars)
                            except Exception:
                                custo = None
                            custos_preview.append(custo)
                        # Atribuir no DataFrame na ordem dos itens
                        if len(custos_preview) == len(df):
                            df['custo_preview_regra'] = custos_preview
                            st.caption("🧮 Pré-visualização: coluna 'custo_preview_regra' mostra o custo calculado por item usando a regra atual.")
                    else:
                        st.caption("ℹ️ Para ver a pré-visualização com a regra, salve a regra ou gere uma fórmula no bloco de criação/edição.")
                except Exception:
                    # Evita travar preview caso a regra ainda não esteja disponível
                    pass

                # Mostrar colunas principais + impostos e rateios para depuração
                cols_basicas = ['codigo', 'sku', 'descricao', 'quantidade', 'vUnCom', 'vProd', 'custo_unit_sugerido', 'custo_preview_regra']
                cols_debug = ['ipi_total', 'ipi_aliq', 'rateio_frete', 'frete_unit', 'rateio_seguro', 'seguro_unit', 'rateio_outros', 'outros_unit', 'rateio_desconto', 'desconto_unit']
                cols_existentes = [c for c in cols_basicas + cols_debug if c in df.columns]
                edited = st.data_editor(
                    df[cols_existentes + (["sku_override"] if "sku_override" in df.columns else [])],
                    use_container_width=True,
                    hide_index=True,
                    disabled=[c for c in cols_existentes if c != "sku_override"],
                    key="editor_itens_xml"
                )
                # Persistir overrides para uso nos fluxos de verificação/atualização
                try:
                    st.session_state['itens_overrides_xml'] = edited[['codigo','sku','descricao','sku_override']].to_dict('records')
                except Exception:
                    st.session_state['itens_overrides_xml'] = []
                # Destaque do primeiro item com breakdown
                if len(nfe.itens) > 0:
                    it0 = nfe.itens[0]
                    frete_unit0 = (it0.rateio_frete / it0.quantidade) if it0.quantidade else 0.0
                    ipi_unit0 = (it0.ipi / it0.quantidade) if it0.quantidade else 0.0
                    st.caption(f"🔎 Primeiro item: frete unitário R$ {frete_unit0:.2f} • IPI unitário R$ {ipi_unit0:.2f} • vUnCom R$ {it0.vUnCom:.2f}")
            
            # Formulário para criar/editar regra de custo
            st.markdown("---")
            st.markdown("### 🧮 Regra de Cálculo de Custo")
            
            # Controle de expansão: sempre expandido se editando, ou se não tem regra, ou se clicou em editar
            deve_expandir = (not regra_existente) or st.session_state.get('editar_regra_xml', False)
            
            with st.expander("➕ Criar/Editar Regra para este Fornecedor", expanded=deve_expandir):
                
                # Opção de modo: Assistido ou Manual
                modo_regra = st.radio(
                    "Modo de Criação da Regra",
                    ["🎯 Assistido (Recomendado)", "✍️ Manual (Fórmula Livre)"],
                    horizontal=True
                )
                # Alternar exibição de debug
                mostrar_debug = st.checkbox("Mostrar variáveis e detalhes de debug", value=False, help="Exibe detalhes da fórmula e valores usados no teste")
                
                if modo_regra == "🎯 Assistido (Recomendado)":
                    usar_frete_flag = None  # para logging fora do escopo
                    st.markdown("### Configure os componentes do custo:")
                    st.caption("Marque os itens que devem compor o custo final e defina os ajustes")
                    
                    col_comp1, col_comp2 = st.columns(2)
                    
                    with col_comp1:
                        st.markdown("**Base de Cálculo:**")
                        usar_vuncom = st.checkbox("Valor Unitário Comercial", value=True, help="vUnCom do XML")
                        if usar_vuncom:
                            operacao_vuncom = st.radio("Operação", ["Multiplicar por", "Dividir por"], horizontal=True, key="op_vuncom")
                            fator_vuncom = st.number_input(
                                operacao_vuncom, 
                                min_value=0.01, 
                                value=1.0, 
                                step=0.1, 
                                help="Ex: 7 para dividir por 7, ou 1.15 para multiplicar por 1.15",
                                key="fator_vuncom"
                            )
                        
                        st.markdown("**Impostos:**")
                        usar_ipi = st.checkbox("IPI", value=False, help="Incluir IPI no custo (sempre ajustado proporcionalmente)")
                        if usar_ipi:
                            tipo_ipi = st.radio("Forma de cálculo IPI", ["Ajustar IPI proporcionalmente", "Somar alíquota % ao valor unitário", "Somar valor total do IPI"], horizontal=False, key="tipo_ipi")
                            if tipo_ipi == "Somar alíquota % ao valor unitário":
                                st.caption("Ex: se vUnCom = 20 e IPI = 6,5%, resultado = 20 * 1.065 = 21.30")
                            elif tipo_ipi == "Ajustar IPI proporcionalmente":
                                st.caption("💡 Padrão: Se valor unitário ÷7, IPI ×7. Se valor ×2, IPI ÷2")
                            else:
                                multiplicador_ipi = st.number_input("% do IPI a somar", min_value=0.0, value=100.0, step=1.0, help="Ex: 70 para somar 70% do IPI total", key="mult_ipi") / 100
                        
                        usar_st = st.checkbox("ICMS ST", value=False, help="Incluir ST no custo (sempre ajustado proporcionalmente)")
                        usar_icms = st.checkbox("ICMS", value=False, help="Incluir ICMS no custo (sempre ajustado proporcionalmente)")
                    
                    with col_comp2:
                        st.markdown("**Rateios:**")
                        usar_frete = st.checkbox("Frete", value=True, help="Rateio de frete")
                        usar_seguro = st.checkbox("Seguro", value=True, help="Rateio de seguro")
                        usar_outros = st.checkbox("Outras despesas", value=True, help="Rateio de outros")
                        usar_desconto = st.checkbox("Desconto (subtrair)", value=True, help="Rateio de desconto")
                        usar_frete_flag = usar_frete
                        
                        st.markdown("**Impostos Federais:**")
                        usar_pis = st.checkbox("PIS", value=False, help="Incluir PIS no custo (sempre ajustado proporcionalmente)")
                        usar_cofins = st.checkbox("COFINS", value=False, help="Incluir COFINS no custo (sempre ajustado proporcionalmente)")
                    
                    # Aviso se frete foi ajustado mas não será incluído
                    try:
                        frete_atual_para_formula = float(nfe.vFrete)
                    except Exception:
                        frete_atual_para_formula = 0.0
                    if frete_atual_para_formula > 0 and not usar_frete:
                        st.warning("Frete ajustado diferente de zero, mas a opção 'Frete' está desmarcada. Ele não será somado ao custo.")

                    # Gerar fórmula automaticamente
                    formula_partes = []
                    
                    # Base
                    if usar_vuncom:
                        if fator_vuncom != 1.0:
                            if operacao_vuncom == "Dividir por":
                                base_formula = f"(vUnCom / {fator_vuncom})"
                            else:  # Multiplicar por
                                base_formula = f"(vUnCom * {fator_vuncom})"
                        else:
                            base_formula = "vUnCom"
                        
                        formula_partes.append(base_formula)
                    
                    # Impostos por unidade (SEMPRE ajustados proporcionalmente)
                    impostos_unit = []
                    
                    # Função auxiliar para ajustar imposto proporcionalmente
                    def ajustar_imposto(imposto_base):
                        if usar_vuncom and fator_vuncom != 1.0:
                            if operacao_vuncom == "Dividir por":
                                return f"(({imposto_base}) * {fator_vuncom})"
                            else:  # Multiplicar por
                                return f"(({imposto_base}) / {fator_vuncom})"
                        return f"({imposto_base})"
                    
                    if usar_ipi and 'tipo_ipi' in locals():
                        if tipo_ipi == "Somar alíquota % ao valor unitário":
                            # Calcula IPI sobre vProd e divide pela quantidade (sem ajuste proporcional)
                            impostos_unit.append("((vProd * ipi_aliq / 100) / quantidade)")
                        elif tipo_ipi == "Somar valor total do IPI":
                            if 'multiplicador_ipi' in locals() and multiplicador_ipi != 1.0:
                                impostos_unit.append(ajustar_imposto(f"ipi_total / quantidade * {multiplicador_ipi}"))
                            else:
                                impostos_unit.append(ajustar_imposto("ipi_total / quantidade"))
                        elif tipo_ipi == "Ajustar IPI proporcionalmente":
                            impostos_unit.append(ajustar_imposto("ipi_total / quantidade"))
                    
                    if usar_st:
                        impostos_unit.append(ajustar_imposto("st_total / quantidade"))
                    
                    if usar_icms:
                        impostos_unit.append(ajustar_imposto("icms_total / quantidade"))
                    
                    if usar_pis:
                        impostos_unit.append(ajustar_imposto("pis_total / quantidade"))
                    
                    if usar_cofins:
                        impostos_unit.append(ajustar_imposto("cofins_total / quantidade"))
                    
                    # Rateios por unidade
                    rateios_unit = []
                    if usar_frete:
                        rateios_unit.append("(rateio_frete / quantidade)")
                    if usar_seguro:
                        rateios_unit.append("(rateio_seguro / quantidade)")
                    if usar_outros:
                        rateios_unit.append("(rateio_outros / quantidade)")
                    
                    # Montar fórmula
                    formula_input = " + ".join(formula_partes + impostos_unit + rateios_unit)
                    if usar_desconto:
                        formula_input += " - (rateio_desconto / quantidade)"
                    
                    if not formula_input:
                        formula_input = "vUnCom"  # fallback
                    
                    st.markdown("**Fórmula Gerada:**")
                    st.code(formula_input, language="python")
                    # Logar a fórmula gerada e se frete foi marcado
                    try:
                        logger.info(f"[XML Upload] Fórmula gerada: {formula_input} | usar_frete={usar_frete_flag}")
                    except Exception:
                        pass
                    
                    # Debug: mostrar componentes (opcional)
                    if mostrar_debug:
                        with st.expander("🔍 Detalhes da Fórmula", expanded=False):
                            st.write("**Base:**", formula_partes)
                            st.write("**Impostos:**", impostos_unit)
                            st.write("**Rateios:**", rateios_unit)
                            st.write("**Fórmula final:**", formula_input)
                
                else:  # Modo Manual
                    st.markdown("""
                    **Variáveis disponíveis:**
                    - `vUnCom`: valor unitário comercial
                    - `quantidade`: quantidade do item
                    - `vProd`: valor total do produto
                    - `ipi_total`: IPI total do item
                    - `ipi_aliq`: alíquota IPI em % (auto-calculada)
                    - `st_total`, `icms_total`, `pis_total`, `cofins_total`
                    - `rateio_frete`, `rateio_seguro`, `rateio_outros`, `rateio_desconto`
                    
                    **Exemplo:** `(vUnCom / 7) + (ipi_aliq * 0.7)`
                    """)
                    
                    formula_default = regra_existente['formula'] if regra_existente else ''
                    formula_input = st.text_area(
                        "Fórmula de Custo",
                        value=formula_default,
                        height=100,
                        help="Digite a fórmula usando as variáveis disponíveis",
                        placeholder="Exemplo: (vUnCom / 7) + (ipi_aliq * 0.7)"
                    )
                
                obs_default = regra_existente['observacoes'] if regra_existente else f'Criada a partir de NF-e {nfe.numero}'
                ativo_default = regra_existente['ativo'] if regra_existente else True
                
                # Mensagem de modo de edição
                if regra_existente and st.session_state.get('editar_regra_xml', False):
                    st.info(f"✏️ **Modo de Edição** - Modificando regra existente para '{nfe.emitente}'")
                
                with st.form("criar_regra_custo"):
                    # Exibir fórmula gerada (read-only no modo assistido)
                    if modo_regra == "🎯 Assistido (Recomendado)":
                        st.text_area("Fórmula Final", value=formula_input, height=80, disabled=True, help="Fórmula gerada automaticamente")
                    
                    obs_input = st.text_input("Observações", value=obs_default)
                    ativo = st.checkbox("Ativar regra", value=ativo_default)
                    
                    col_btn1, col_btn2, col_btn3 = st.columns(3)
                    with col_btn1:
                        salvar_regra = st.form_submit_button("💾 Salvar Regra", width='stretch', type="primary")
                    with col_btn2:
                        testar_formula = st.form_submit_button("🧪 Testar Fórmula", width='stretch')
                    with col_btn3:
                        if regra_existente:
                            cancelar = st.form_submit_button("❌ Cancelar", width='stretch')
                        else:
                            usar_padrao = st.form_submit_button("📊 Usar Padrão", width='stretch')
                    
                    if salvar_regra and formula_input:
                        try:
                            add_or_update_regra_custo(
                                fornecedor=nfe.emitente,
                                formula=formula_input,
                                ativo=ativo,
                                observacoes=obs_input
                            )
                            acao = "atualizada" if regra_existente else "criada"
                            st.success(f"✅ Regra {acao} para '{nfe.emitente}'!")
                            st.info("💡 A regra será aplicada automaticamente em futuras importações deste fornecedor")
                            st.session_state['editar_regra_xml'] = False
                            st.rerun()
                        except Exception as e:
                            st.error(f"Erro ao salvar regra: {e}")
                    
                    if testar_formula and formula_input:
                        # Testar fórmula com primeiro item da NF-e
                        try:
                            from modules.regras_custo import RegraFornecedorCusto
                            if nfe.itens:
                                item_teste = nfe.itens[0]
                                item_vars = {
                                    'vUnCom': item_teste.vUnCom,
                                    'quantidade': item_teste.quantidade,
                                    'vProd': item_teste.vProd,
                                    'ipi_total': item_teste.ipi,
                                    'ipi_aliq': item_teste.ipi_aliq,
                                    'st_total': item_teste.st,
                                    'icms_total': item_teste.icms,
                                    'pis_total': item_teste.pis,
                                    'cofins_total': item_teste.cofins,
                                    'rateio_frete': item_teste.rateio_frete,
                                    'rateio_seguro': item_teste.rateio_seguro,
                                    'rateio_outros': item_teste.rateio_outros,
                                    'rateio_desconto': item_teste.rateio_desconto
                                }
                                # Debug: mostrar valores das variáveis (opcional)
                                if mostrar_debug:
                                    st.info(
                                        "🔍 Debug: "
                                        f"vUnCom={item_vars['vUnCom']:.4f}, "
                                        f"vProd={item_vars['vProd']:.2f}, "
                                        f"quantidade={item_vars['quantidade']:.0f}, "
                                        f"ipi_aliq={item_vars['ipi_aliq']:.2f}, "
                                        f"rateio_frete={item_vars['rateio_frete']:.4f}, "
                                        f"frete_unit={(item_vars['rateio_frete']/item_vars['quantidade']) if item_vars['quantidade'] else 0.0:.4f}"
                                    )
                                # Logar variáveis-chave do teste
                                try:
                                    logger.info(
                                        f"[XML Upload] Teste fórmula | modo='{modo_regra}' | usar_frete={usar_frete_flag} | "
                                        f"vUnCom={item_vars['vUnCom']:.4f} | vProd={item_vars['vProd']:.2f} | qtd={item_vars['quantidade']:.0f} | "
                                        f"ipi_aliq={item_vars['ipi_aliq']:.2f} | rateio_frete={item_vars['rateio_frete']:.6f} | vFrete_total={nfe.vFrete:.2f}"
                                    )
                                except Exception:
                                    pass

                                regra_teste = RegraFornecedorCusto(
                                    fornecedor=nfe.emitente,
                                    formula=formula_input,
                                    ativo=True
                                )
                                resultado = regra_teste.calcular_custo(item_vars)
                                st.success(f"✅ Fórmula válida! Resultado teste (1º item): R$ {resultado:.2f}")
                                try:
                                    logger.info(f"[XML Upload] Resultado teste (1º item): {resultado:.6f}")
                                except Exception:
                                    pass
                                st.caption(f"Item teste: {item_teste.descricao[:50]}... (vUnCom: R$ {item_teste.vUnCom:.2f})")
                            else:
                                st.warning("Sem itens para testar")
                        except Exception as e:
                            st.error(f"❌ Erro na fórmula: {e}")
                    
                    if regra_existente and 'cancelar' in locals() and cancelar:
                        st.session_state['editar_regra_xml'] = False
                        st.rerun()
                    
                    if not regra_existente and 'usar_padrao' in locals() and usar_padrao:
                        st.info("📊 Usando cálculo padrão (vUnCom + rateios + impostos)")
                    
                    # Evita NameError quando o botão não existe (regra existente)
                    if 'usar_padrao' in locals() and usar_padrao:
                        st.info("📊 Usando cálculo padrão (vUnCom + rateios + impostos)")
            
            # Download CSV
            st.markdown("---")
            st.markdown("### 📥 Exportar Dados")
            
            rows_export = to_rows(nfe)
            import pandas as pd
            df_export = pd.DataFrame(rows_export)
            csv = df_export.to_csv(index=False)
            
            st.download_button(
                label="📥 Download CSV dos Itens",
                data=csv,
                file_name=f"nfe_{nfe.numero}_itens.csv",
                mime="text/csv"
            )
            
            st.caption("💡 Use a seção 'Enviar NF-e com custos ajustados' abaixo para incluir a nota no Tiny com os valores calculados pela regra")

            # Fluxo: Enviar NF-e com custos ajustados pela regra
            st.markdown("---")
            st.markdown("### 🚀 Enviar NF-e para o Tiny com custos ajustados")
            st.info("💡 Este fluxo envia a NF-e para o Tiny substituindo os valores unitários (vUnCom) pelos custos calculados pela regra. O Tiny registrará a nota com esses valores ajustados.")
            
            st.markdown("---")
            st.markdown("### 📤 Enviar NF-e para o Tiny")
            st.caption("ÚNICA forma via API de adicionar na aba Custos")
            
            # Escolher modo de geração
            st.markdown("#### 🔧 Modo de Geração do XML")
            
            # Alerta de recomendação
            st.success("""
            ✅ **RECOMENDADO:** Use **"Gerar XML Completo"**
            - Estrutura validada e testada
            - ICMS 20%, FCP 2%, IPI 0%
            - Compatibilidade garantida com Tiny
            - Baseado no seu script que já funciona
            """)
            
            modo_xml = st.radio(
                "Escolha como gerar o XML:",
                options=["gerar_completo", "modificar"],
                format_func=lambda x: {
                    "gerar_completo": "✅ Gerar XML Completo (RECOMENDADO - estrutura validada)",
                    "modificar": "📝 Modificar XML Original (experimental)"
                }[x],
                index=0,  # Padrão = gerar_completo
                help="Modificar: Altera apenas os valores no XML original. Gerar Completo: Cria XML do zero.",
                key="modo_xml_nfe"
            )
            
            if modo_xml == "gerar_completo":
                st.info("""
                ✅ **XML Completo** - Estrutura validada que já funciona:
                - ICMS 20%, FCP 2%, IPI 0% (configurável)
                - Todos os campos obrigatórios
                - Baseado no script que você já usa
                - Maior compatibilidade com Tiny
                """)
            else:
                st.info("""
                📝 **Modificar Original** - Mantém estrutura da nota:
                - Preserva emitente, destinatário, impostos originais
                - Altera APENAS os valores unitários (vUnCom)
                - Recalcula vProd automaticamente
                """)
            
            # Validar tipo de nota
            modelo_valido = nfe.modelo == '55'
            finalidade_valida = nfe.finalidade == '1'
            
            if not modelo_valido:
                st.error(f"❌ **Nota incompatível:** Modelo {nfe.modelo} não suportado pelo Tiny")
                st.info("""
                ℹ️ **O Tiny só aceita NF-e modelo 55 (mercadorias)**
                
                Modelos não suportados:
                - **55**: NF-e de produtos (✅ COMPATÍVEL)
                - **65**: NFC-e (Consumidor final) ❌
                - Outros modelos ❌
                
                **Solução:** Use apenas NF-e de entrada de mercadorias (modelo 55)
                """)
            elif not finalidade_valida:
                st.warning(f"⚠️ **Finalidade {nfe.finalidade}:** Pode não atualizar custos corretamente")
                st.caption("Finalidades: 1=Normal, 2=Complementar, 3=Ajuste, 4=Devolução")
            else:
                st.info("""
                📝 **Como funciona (CONFIRMADO pela doc Tiny):**
                1. Modifica XML substituindo `vUnCom` pelos custos calculados
                2. Envia via `incluir.nota.xml`
                3. **Tiny cria linhas na aba "Custos"** automaticamente
                
                ✅ **Confirmado:** `produto.atualizar.estoque` com qtd=0 NÃO cria registros (doc Tiny).
                Esta é a ÚNICA forma via API.
                """)
                
                st.warning("""
                ⚠️ **IMPORTANTE:**
                - CRIA nova nota no Tiny (verificar duplicação!)
                - Valores serão os calculados, NÃO os originais
                """)
            
            enviar_nfe_mod = st.checkbox("✅ Confirmo envio da NF-e modificada", value=False, key="confirma_nfe_mod", disabled=not modelo_valido)
            
            col_btn1, col_btn2 = st.columns(2)
            with col_btn1:
                btn_preview = st.button("👁️ Preview XML (sem enviar)", disabled=not modelo_valido)
            with col_btn2:
                btn_enviar = st.button("📤 Enviar NF-e para Tiny", type="primary", disabled=(not enviar_nfe_mod or not modelo_valido))
            
            # Preview do XML (antes de enviar)
            if btn_preview:
                try:
                    from modules.regras_custo import RegraFornecedorCusto
                    from modules.nfe_modifier import modificar_xml_nfe_com_custos
                    from modules.nfe_generator import gerar_nfe_completa
                    
                    # Verificar regra
                    regra_para_aplicar = None
                    if regra_existente and regra_existente.get('ativo') and regra_existente.get('formula'):
                        regra_para_aplicar = RegraFornecedorCusto(
                            fornecedor=nfe.emitente,
                            formula=regra_existente['formula'],
                            ativo=True
                        )
                    
                    if not regra_para_aplicar:
                        st.error("❌ Defina e ative uma regra de custo primeiro")
                    else:
                        # Calcular custos
                        custos_por_sku = {}
                        for it in nfe.itens:
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
                                'rateio_desconto': it.rateio_desconto
                            }
                            try:
                                custo = regra_para_aplicar.calcular_custo(item_vars)
                                # USAR cProd (código) como chave - sempre existe!
                                codigo = str(it.codigo)
                                custos_por_sku[codigo] = custo
                            except Exception as e:
                                st.warning(f"Erro calculando custo {it.codigo}: {e}")
                        
                        # Gerar XML
                        if modo_xml == "gerar_completo":
                            xml_preview = gerar_nfe_completa(nfe, custos_por_sku)
                        else:
                            xml_content = xml_bytes.decode('utf-8')
                            xml_preview = modificar_xml_nfe_com_custos(xml_content, custos_por_sku)
                        
                        st.success(f"✅ XML gerado com sucesso! {len(custos_por_sku)} itens processados")
                        
                        # Mostrar primeiras linhas para verificar
                        with st.expander("📄 Primeiras 100 linhas do XML gerado", expanded=True):
                            linhas = xml_preview.split('\n')[:100]
                            st.code('\n'.join(linhas), language="xml")
                        
                        # Botão download
                        st.download_button(
                            "💾 Baixar XML Completo",
                            xml_preview,
                            file_name=f"nfe_preview_{nfe.numero}.xml",
                            mime="application/xml"
                        )
                        
                        # Comparar campos importantes
                        st.markdown("#### 🔍 Verificação de Campos Importantes")
                        if '<mod>55</mod>' in xml_preview or '<mod>55' in xml_preview:
                            st.success("✅ Modelo 55 confirmado no XML")
                        else:
                            st.error("❌ Modelo 55 NÃO encontrado!")
                        
                        if '<finNFe>1</finNFe>' in xml_preview or '<finNFe>1' in xml_preview:
                            st.success("✅ Finalidade 1 (Normal) confirmada")
                        else:
                            st.warning("⚠️ Finalidade pode estar diferente de 1")
                
                except Exception as e:
                    st.error(f"❌ Erro ao gerar preview: {e}")
                    import traceback
                    st.code(traceback.format_exc())
            
            if btn_enviar:
                try:
                    from modules.regras_custo import RegraFornecedorCusto
                    from modules.nfe_modifier import modificar_xml_nfe_com_custos
                    from modules.nfe_generator import gerar_nfe_completa
                    from modules.tiny_api import incluir_nota_xml
                    
                    # Verificar regra
                    regra_para_aplicar = None
                    if regra_existente and regra_existente.get('ativo') and regra_existente.get('formula'):
                        regra_para_aplicar = RegraFornecedorCusto(
                            fornecedor=nfe.emitente,
                            formula=regra_existente['formula'],
                            ativo=True
                        )
                    
                    if not regra_para_aplicar:
                        st.error("❌ Defina e ative uma regra de custo primeiro")
                    else:
                        progress = st.progress(0)
                        status = st.empty()
                        
                        # Calcular custos por SKU
                        status.text("Calculando custos...")
                        progress.progress(0.2)
                        
                        custos_por_sku = {}
                        for it in nfe.itens:
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
                                'rateio_desconto': it.rateio_desconto
                            }
                            try:
                                custo = regra_para_aplicar.calcular_custo(item_vars)
                                # USAR cProd (código) como chave - sempre existe!
                                codigo = str(it.codigo)
                                custos_por_sku[codigo] = custo
                            except Exception as e:
                                st.warning(f"Erro calculando custo {it.codigo}: {e}")
                        
                        # Gerar ou modificar XML
                        status.text("Gerando XML..." if modo_xml == "gerar_completo" else "Modificando XML...")
                        progress.progress(0.4)
                        
                        if modo_xml == "gerar_completo":
                            # Gerar XML completo do zero
                            xml_final = gerar_nfe_completa(nfe, custos_por_sku)
                        else:
                            # Modificar XML original
                            xml_content = xml_bytes.decode('utf-8')
                            xml_final = modificar_xml_nfe_com_custos(xml_content, custos_por_sku)
                        
                        # Preview do XML gerado
                        with st.expander("🔍 Ver XML que será enviado"):
                            st.code(xml_final[:2000] + "..." if len(xml_final) > 2000 else xml_final, language="xml")
                        
                        # Enviar para Tiny
                        status.text("Enviando para o Tiny...")
                        progress.progress(0.6)
                        
                        resultado = incluir_nota_xml(xml_final, lancar_estoque=False, lancar_contas=False)
                        
                        progress.progress(1.0)
                        
                        if resultado.get('ok'):
                            st.success(f"""
                            ✅ **NF-e enviada com sucesso!**
                            - {len(custos_por_sku)} itens processados
                            - Modo: {'XML Completo Gerado' if modo_xml == 'gerar_completo' else 'XML Original Modificado'}
                            - Custos calculados pela regra de '{nfe.emitente}'
                            """)
                            st.info("💡 Verifique a **Aba Custos** no Tiny para confirmar os registros criados")
                        else:
                            st.error(f"❌ Erro ao enviar: {resultado.get('data')}")
                
                except Exception as e:
                    st.error(f"❌ Erro: {e}")
                except Exception as e:
                    st.error(f"❌ Erro: {e}")
                    logger.exception("Erro ao enviar NF-e modificada")
        
        except Exception as e:
            st.error(f"Erro ao processar XML: {e}")
            import traceback
            with st.expander("Ver detalhes do erro"):
                st.code(traceback.format_exc())
        finally:
            # Limpar arquivo temporário
            try:
                os.unlink(tmp_path)
            except:
                pass
