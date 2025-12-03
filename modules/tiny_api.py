def _normalize_text(s: str) -> str:
    """Remove acentos, normaliza espaços e caixa para matching mais robusto."""
    import unicodedata
    s = unicodedata.normalize("NFKD", s)
    s = "".join(ch for ch in s if not unicodedata.combining(ch))
    s = s.lower().strip()
    return " ".join(s.split())


def _rate_limit_sleep():
    """Aguarda tempo mínimo entre chamadas à API para respeitar rate limit."""
    time.sleep(0.2)  # 200ms entre chamadas


import requests, json
import time
import logging
from typing import Any, Dict
from . import config

logger = logging.getLogger('tiny_api')
BASE_URL = "https://api.tiny.com.br/api2"
TOKEN = config.TINY_API_TOKEN

def listar_produtos(page=1, pesquisa=""):
    """Lista produtos do Tiny ERP com error handling robusto
    
    Args:
        page: Número da página (padrão 100 registros por página)
        pesquisa: Nome ou código do produto (obrigatório na API, use "" para listar todos)
    
    Returns:
        Dict com retorno.produtos ou error
    """
    if not config.TINY_API_TOKEN:
        logger.warning('TINY_API_TOKEN not configured')
        return {'error': 'Token não configurado', 'retorno': {'produtos': []}}
    
    params = {
        "token": config.TINY_API_TOKEN, 
        "formato": "json", 
        "pagina": page,
        "pesquisa": pesquisa  # Obrigatório na API Tiny
    }
    
    try:
        logger.debug(f'Tiny API: produtos página {page}')
        r = requests.get(f"{BASE_URL}/produtos.pesquisa.php", params=params, timeout=30)
        r.raise_for_status()
        
        data = r.json()
        retorno = data.get('retorno', {})
        produtos = retorno.get('produtos', [])
        logger.info(f'Tiny API: {len(produtos)} produtos retornados (página {page}/{retorno.get("numero_paginas", 1)})')
        return data
    
    except requests.exceptions.Timeout:
        logger.error('Tiny API timeout')
        return {'error': 'Timeout na requisição', 'retorno': {'produtos': []}}
    except requests.exceptions.RequestException as e:
        logger.error(f'Tiny API error: {e}', exc_info=True)
        return {'error': str(e), 'retorno': {'produtos': []}}
    except Exception as e:
        logger.error(f'Unexpected error: {e}', exc_info=True)
        return {'error': 'Erro inesperado', 'retorno': {'produtos': []}}

def obter_produto_por_sku(sku: str):
    """Obtém detalhes de um produto do Tiny ERP pelo SKU (código).

    Retorna dict com campos relevantes quando encontrado:
    - preco_custo
    - preco
    - codigo
    - nome
    Caso não encontrado, retorna {'error': '...'}.
    """
    if not config.TINY_API_TOKEN:
        logger.warning('TINY_API_TOKEN not configured')
        return {'error': 'Token não configurado'}

    params = {
        "token": config.TINY_API_TOKEN,
        "formato": "json",
        "pesquisa": sku,
    }

    try:
        r = requests.get(f"{BASE_URL}/produtos.pesquisa.php", params=params, timeout=30)
        r.raise_for_status()
        data = r.json()
        produtos = (data.get('retorno') or {}).get('produtos') or []
        if not produtos:
            return {'error': 'Produto não encontrado'}
        # Estrutura: cada item tem {'produto': {...}}
        prod_info = produtos[0].get('produto') or {}
        return {
            'codigo': prod_info.get('codigo'),
            'nome': prod_info.get('nome'),
            'preco': _safe_float(prod_info.get('preco')),
            'preco_custo': _safe_float(prod_info.get('preco_custo')),
            'raw': prod_info
        }
    except Exception as e:
        logger.error(f'Erro ao obter produto por SKU {sku}: {e}', exc_info=True)
        return {'error': str(e)}

def obter_produto_detalhado(codigo: str) -> Dict[str, Any]:
    """Obtém um produto detalhado pelo código (SKU) usando produtos.obter.

    Retorna dict com campos relevantes incluindo preco_custo se presentes.
    """
    if not config.TINY_API_TOKEN:
        logger.warning('TINY_API_TOKEN not configured')
        return {'error': 'Token não configurado'}

    params = {
        "token": config.TINY_API_TOKEN,
        "formato": "json",
        "codigo": codigo,
    }

    try:
        r = requests.get(f"{BASE_URL}/produtos.obter.php", params=params, timeout=30)
        r.raise_for_status()
        data = r.json()
        produto = (data.get('retorno') or {}).get('produto') or {}
        if not produto:
            return {'error': 'Produto não encontrado'}
        return {
            'codigo': produto.get('codigo'),
            'nome': produto.get('nome'),
            'preco': _safe_float(produto.get('preco')),
            'preco_custo': _safe_float(produto.get('preco_custo')),
            'raw': produto,
        }
    except Exception as e:
        logger.error(f'Erro ao obter produto detalhado {codigo}: {e}', exc_info=True)
        return {'error': str(e)}

def obter_produto_por_sku_ou_nome(sku: str = "", descricao: str = ""):
    """Obtém detalhes de um produto do Tiny ERP tentando primeiro pelo SKU (codigo)
    e, se não encontrar, tentando pelo nome/descrição.

    Retorna dict com:
    - codigo, nome, preco, preco_custo, raw
    Ou {'error': '...'} quando não encontrado/erro.
    Estratégia:
    1) Pesquisa por SKU usando produtos.pesquisa.php (pesquisa=codigo).
       - Se múltiplos resultados, tenta match exato pelo campo 'codigo'.
    2) Se não encontrado, pesquisa por 'descricao' (nome parcial).
       - Se múltiplos resultados, tenta o primeiro cujo 'nome' contenha a descrição (case-insensitive).
    """
    if not config.TINY_API_TOKEN:
        logger.warning('TINY_API_TOKEN not configured')
        return {'error': 'Token não configurado'}

    def _from_prod_info(prod_info: dict):
        return {
            'id': prod_info.get('id'),
            'codigo': prod_info.get('codigo'),  # SKU usado em produto.alterar.php
            'nome': prod_info.get('nome'),
            'preco': _safe_float(prod_info.get('preco')),
            'preco_custo': _safe_float(prod_info.get('preco_custo')),
            'raw': prod_info
        }

    # 1) Tentar por SKU
    if sku:
        try:
            params = {"token": config.TINY_API_TOKEN, "formato": "json", "pesquisa": sku}
            r = requests.get(f"{BASE_URL}/produtos.pesquisa.php", params=params, timeout=30)
            r.raise_for_status()
            data = r.json()
            produtos = (data.get('retorno') or {}).get('produtos') or []
            # Tenta match exato por codigo
            for p in produtos:
                prod_info = p.get('produto') or {}
                if str(prod_info.get('codigo') or '').strip() == str(sku).strip():
                    return _from_prod_info(prod_info)
            # Se não achou exato mas veio algo, retorna o primeiro
            if produtos:
                return _from_prod_info(produtos[0].get('produto') or {})
        except Exception as e:
            logger.error(f'Erro na busca por SKU {sku}: {e}', exc_info=True)

    # 2) Tentar por descrição/nome
    if descricao:
        try:
            params = {"token": config.TINY_API_TOKEN, "formato": "json", "pesquisa": descricao}
            r = requests.get(f"{BASE_URL}/produtos.pesquisa.php", params=params, timeout=30)
            r.raise_for_status()
            data = r.json()
            produtos = (data.get('retorno') or {}).get('produtos') or []
            # Fuzzy match com normalização de texto
            if produtos:
                from difflib import SequenceMatcher
                desc_norm = _normalize_text(str(descricao))
                melhor = None
                melhor_score = 0.0
                for p in produtos:
                    prod_info = p.get('produto') or {}
                    nome = str(prod_info.get('nome') or '')
                    nome_norm = _normalize_text(nome)
                    score = SequenceMatcher(None, desc_norm, nome_norm).ratio()
                    if score > melhor_score:
                        melhor_score = score
                        melhor = prod_info
                # Threshold conservador
                if melhor and melhor_score >= 0.6:
                    return _from_prod_info(melhor)
                # Fallback: primeiro resultado
                return _from_prod_info(produtos[0].get('produto') or {})
        except Exception as e:
            logger.error(f'Erro na busca por descricao "{descricao}": {e}', exc_info=True)

    return {'error': 'Produto não encontrado por SKU ou descrição'}

def _safe_float(val):
    try:
        if val is None:
            return 0.0
        if isinstance(val, (int, float)):
            return float(val)
        # valores podem vir como string com vírgula
        s = str(val).replace('.', '').replace(',', '.') if isinstance(val, str) else str(val)
        return float(s)
    except Exception:
        return 0.0

def _format_preco_custo(valor: Any) -> str:
    """Formata o preço de custo com ponto decimal e 2-4 casas conforme aceito pela Tiny."""
    try:
        f = float(str(valor).replace(',', '.'))
    except Exception:
        f = 0.0
    # Tiny aceita ponto como separador decimal. Enviar como string para evitar locale issues.
    return f"{f:.4f}".rstrip('0').rstrip('.') if f % 1 != 0 else f"{int(f)}"

def atualizar_preco_custo(codigo: str, preco_custo: Any, max_retries: int = 3, base_sleep: float = 1.0) -> Dict[str, Any]:
    """Atualiza preço de custo no Tiny com retry e logging detalhado e captura de headers.

    Retorna dict com chaves: ok, status_code, data, text, tentativa, waited, x_limit_api, x_remaining_api
    """
    import json as _json
    url = f"{BASE_URL}/produto.alterar.php"
    params = {"token": TOKEN, "formato": "json"}
    produto_payload = {
        "codigo": str(codigo).strip(),
        # Tiny aceita preco_custo no alterar produto
        "preco_custo": _format_preco_custo(preco_custo),
    }

    tentativa = 0
    waited = 0.0
    result = None
    while tentativa < max_retries:
        tentativa += 1
        try:
            # Tiny espera 'produto' como campo de formulário contendo JSON em string
            resp = requests.post(
                url,
                params=params,
                data={"produto": _json.dumps(produto_payload)},
                timeout=20
            )
            # Captura limites se presentes
            x_limit_api = resp.headers.get("x-limit-api")
            x_remaining_api = resp.headers.get("x-remaining-api")

            try:
                data = resp.json()
            except Exception:
                data = {"erro": True, "mensagem": resp.text}

            status = (data.get("status") or data.get("retorno", {}).get("status") or "").upper()
            erros = data.get("erro") or data.get("retorno", {}).get("erros")

            ok = bool(status == "OK" and not erros)
            result = {
                "ok": ok,
                "status_code": resp.status_code,
                "data": data,
                "text": resp.text[:2000],
                "tentativa": tentativa,
                "waited": waited,
                "x_limit_api": x_limit_api,
                "x_remaining_api": x_remaining_api,
            }

            # Logging detalhado para auditoria
            retorno = data.get("retorno", {}) if isinstance(data, dict) else {}
            status_proc = retorno.get("status_processamento")
            status_txt = retorno.get("status") or data.get("status")
            codigo_erro = retorno.get("codigo_erro")
            if ok:
                logger.info(f"Tiny produto.alterar OK codigo={codigo} preco_custo={produto_payload['preco_custo']} status_proc={status_proc} x-limit={x_limit_api} x-remain={x_remaining_api}")
            else:
                logger.warning(f"Tiny produto.alterar Falha codigo={codigo} status={status_txt} cod_erro={codigo_erro} http={resp.status_code} x-limit={x_limit_api} x-remain={x_remaining_api} resp={str(data)[:500]}")

            if ok:
                return result

            # Heurística de rate limit: HTTP 429, mensagens, ou codigo_erro=6
            msg = str(data)
            codigo_erro = data.get("retorno", {}).get("codigo_erro")
            is_rate = (
                resp.status_code == 429
                or ("limite" in msg.lower() or "rate" in msg.lower() or "muitas" in msg.lower())
                or (codigo_erro in (6, "6"))
            )
            sleep_s = base_sleep * (2 ** (tentativa - 1)) if is_rate else base_sleep
            time.sleep(sleep_s)
            waited += sleep_s
        except requests.RequestException as e:
            logging.exception("Erro de rede ao atualizar preco_custo no Tiny: %s", e)
            time.sleep(base_sleep)
            waited += base_sleep

    # Última resposta falhou
    return {
        "ok": False,
        "status_code": result.get("status_code") if result else None,
        "data": result.get("data") if result else None,
        "text": result.get("text") if result else None,
        "tentativa": tentativa,
        "waited": waited,
        "x_limit_api": (result or {}).get("x_limit_api"),
        "x_remaining_api": (result or {}).get("x_remaining_api"),
    }

def informar_custo(id_produto: str, custo: Any, quantidade: float = 0.0001, max_retries: int = 3, base_sleep: float = 1.0) -> Dict[str, Any]:
    """Adiciona registro na aba 'Custos' do produto usando produto.atualizar.estoque.
    
    IMPORTANTE: Usa quantidade mínima (0.0001) pois quantidade=0 não cria registro no Tiny.
    
    Args:
        id_produto: ID interno do produto no Tiny (não é o SKU/codigo!)
        custo: Preço de custo a informar
        quantidade: Quantidade mínima (padrão 0.0001 = cria registro com impacto mínimo)
        max_retries: Número máximo de tentativas
        base_sleep: Tempo base de espera entre tentativas
    
    Returns:
        Dict com chaves: ok, status_code, data, tentativa, waited, x_limit_api, x_remaining_api
    """
    url = f"{BASE_URL}/produto.atualizar.estoque.php"
    params = {"token": TOKEN, "formato": "XML"}
    
    # Formata valores - garante quantidade mínima > 0
    custo_fmt = _format_preco_custo(custo)
    qtd_real = max(float(quantidade), 0.0001)  # Força mínimo de 0.0001
    qtd_fmt = f"{qtd_real:.4f}"
    
    # Monta XML conforme documentação Tiny - DEVE usar idProduto, não codigo
    estoque_xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<estoque>
    <idProduto>{str(id_produto).strip()}</idProduto>
    <quantidade>{qtd_fmt}</quantidade>
    <preco_custo>{custo_fmt}</preco_custo>
    <operacao>B</operacao>
</estoque>"""

    tentativa = 0
    waited = 0.0
    result = None
    
    # Log do payload para debug
    logger.info(f"informar_custo: idProduto={id_produto}, quantidade={qtd_fmt}, custo={custo_fmt}")
    
    while tentativa < max_retries:
        tentativa += 1
        _rate_limit_sleep()
        
        try:
            resp = requests.post(
                url,
                params=params,
                data={"estoque": estoque_xml},  # Envia XML no campo 'estoque'
                timeout=30
            )
            
            x_limit_api = resp.headers.get("x-limit-api")
            x_remaining_api = resp.headers.get("x-remaining-api")

            # Resposta é XML, não JSON
            import xml.etree.ElementTree as ET
            try:
                root = ET.fromstring(resp.text)
                status_elem = root.find('.//status')
                status = status_elem.text.upper() if status_elem is not None else ""
                
                # Verifica se há erros
                erros_elem = root.find('.//erros')
                has_errors = erros_elem is not None and len(erros_elem) > 0
                
                data = {
                    "status": status,
                    "xml_response": resp.text,
                    "parsed": True
                }
            except Exception as parse_err:
                logger.warning(f"Erro ao parsear XML: {parse_err}")
                data = {"erro": True, "mensagem": resp.text}
                status = ""
                has_errors = True

            ok = bool(status == "OK" and not has_errors)
            result = {
                "ok": ok,
                "status_code": resp.status_code,
                "data": data,
                "tentativa": tentativa,
                "waited": waited,
                "x_limit_api": x_limit_api,
                "x_remaining_api": x_remaining_api,
            }

            status_txt = data.get("status", "")
            
            if ok:
                logger.info(f"✓ Custo informado: idProduto={id_produto}, custo={custo_fmt}, quantidade={qtd_fmt}")
            else:
                logger.warning(f"Tentativa {tentativa} falhou: status={status_txt}, http={resp.status_code}, resp={str(data)[:300]}")

            if ok:
                return result

            # Heurística de rate limit (simplificada para XML)
            msg = str(data)
            is_rate = (
                resp.status_code == 429
                or ("limite" in msg.lower() or "rate" in msg.lower() or "muitas" in msg.lower())
            )
            
            # Se não é a última tentativa, aguarda
            if tentativa < max_retries:
                sleep_s = base_sleep * (2 ** (tentativa - 1)) if is_rate else base_sleep
                time.sleep(sleep_s)
                waited += sleep_s

        except Exception as e:
            logger.error(f"Erro na tentativa {tentativa}: {e}")
            result = {
                "ok": False,
                "status_code": 0,
                "data": str(e),
                "tentativa": tentativa,
                "waited": waited,
                "x_limit_api": None,
                "x_remaining_api": None
            }
            
            # Se não é a última tentativa, aguarda
            if tentativa < max_retries:
                sleep_s = base_sleep * (2 ** (tentativa - 1))
                time.sleep(sleep_s)
                waited += sleep_s
    
    # Se chegou aqui, esgotou tentativas
    logger.error(f"✗ Falha ao informar custo após {tentativa} tentativas: idProduto={id_produto}")
    return result or {
        "ok": False,
        "status_code": 0,
        "data": "Esgotadas todas as tentativas",
        "tentativa": tentativa,
        "waited": waited,
        "x_limit_api": None,
        "x_remaining_api": None
    }


def listar_pedidos(page=1, data_inicial=None, data_final=None):
    """Lista pedidos do Tiny ERP
    
    Args:
        page: Número da página (padrão 100 registros por página)
        data_inicial: Data inicial no formato dd/mm/yyyy
        data_final: Data final no formato dd/mm/yyyy
    
    Returns:
        Dict com retorno.pedidos ou error
    """
    if not config.TINY_API_TOKEN:
        logger.warning('TINY_API_TOKEN not configured')
        return {'error': 'Token não configurado', 'retorno': {'pedidos': []}}
    
    params = {"token": config.TINY_API_TOKEN, "formato": "json", "pagina": page}
    
    # Pelo menos um parâmetro de filtro é obrigatório na API Tiny
    if not data_inicial and not data_final:
        # Se não informado, pega últimos 30 dias
        from datetime import datetime, timedelta
        data_final_obj = datetime.now()
        data_inicial_obj = data_final_obj - timedelta(days=30)
        data_inicial = data_inicial_obj.strftime('%d/%m/%Y')
        data_final = data_final_obj.strftime('%d/%m/%Y')
    
    if data_inicial:
        params['dataInicial'] = data_inicial
    if data_final:
        params['dataFinal'] = data_final
    
    try:
        logger.debug(f'Tiny API: pedidos página {page} ({data_inicial} a {data_final})')
        r = requests.get(f"{BASE_URL}/pedidos.pesquisa.php", params=params, timeout=30)
        r.raise_for_status()
        
        data = r.json()
        retorno = data.get('retorno', {})
        pedidos = retorno.get('pedidos', [])
        logger.info(f'Tiny API: {len(pedidos)} pedidos retornados (página {page}/{retorno.get("numero_paginas", 1)})')
        return data
    
    except Exception as e:
        logger.error(f'Erro ao listar pedidos: {e}', exc_info=True)
        return {'error': str(e), 'retorno': {'pedidos': []}}

def atualizar_precos_em_massa(precos: list, max_retries: int = 3, base_sleep: float = 1.0) -> Dict[str, Any]:
    """Atualiza preços usando produto.atualizar.precos (em massa).

    Argumento 'precos' deve seguir o layout da API v2 (cada item com identificação do produto e preços/listas).
    Útil para zerar preços atuais ao enviar preco=0 em listas específicas quando desejado.
    """
    url = f"{BASE_URL}/produto.atualizar.precos.php"
    params = {"token": TOKEN, "formato": "json"}
    payload = {"precos": precos}
    tentativa = 0
    waited = 0.0
    last = None
    while tentativa < max_retries:
        tentativa += 1
        try:
            resp = requests.post(url, params=params, json=payload, timeout=30)
            x_limit_api = resp.headers.get("x-limit-api")
            x_remaining_api = resp.headers.get("x-remaining-api")
            try:
                data = resp.json()
            except Exception:
                data = {"erro": True, "mensagem": resp.text}
            retorno = data.get("retorno", {})
            status_txt = (retorno.get("status") or data.get("status") or "").upper()
            status_proc = retorno.get("status_processamento")
            codigo_erro = retorno.get("codigo_erro")
            registros = retorno.get("registros") or []
            ok = status_txt in ("OK", "PARCIAL") and not codigo_erro
            last = {
                "ok": ok,
                "status_code": resp.status_code,
                "data": data,
                "text": resp.text[:2000],
                "tentativa": tentativa,
                "waited": waited,
                "x_limit_api": x_limit_api,
                "x_remaining_api": x_remaining_api,
                "registros": registros,
            }
            if ok:
                logger.info(f"Tiny produto.atualizar.precos status={status_txt} proc={status_proc} x-limit={x_limit_api} x-remain={x_remaining_api}")
                return last
            else:
                logger.warning(f"Tiny produto.atualizar.precos falha status={status_txt} cod_erro={codigo_erro} http={resp.status_code} resp={str(data)[:500]}")
                msg = str(data)
                is_rate = resp.status_code == 429 or (codigo_erro in (6, "6")) or ("muitos" in msg.lower())
                sleep_s = base_sleep * (2 ** (tentativa - 1)) if is_rate else base_sleep
                time.sleep(sleep_s)
                waited += sleep_s
        except requests.RequestException as e:
            logger.exception("Erro de rede ao atualizar preços em massa: %s", e)
            time.sleep(base_sleep)
            waited += base_sleep
    return last or {"ok": False, "tentativa": tentativa, "waited": waited}

def incluir_nota_xml(xml_str: str, lancar_estoque: bool = True, lancar_contas: bool = False, origem: str = "N", max_retries: int = 3, base_sleep: float = 1.0) -> Dict[str, Any]:
    """Inclui uma Nota Fiscal via XML no Tiny e opcionalmente lança estoque/contas.

    Parâmetros:
    - xml_str: conteúdo do XML da NF-e.
    - lancar_estoque: se True, envia 'S' em lancarEstoque.
    - lancar_contas: se True, envia 'S' em lancarContas.
    - origem: 'N' (Nota Fiscal) ou 'P' (Pedido) para origem dos lançamentos.

    Retorna dict com ok, idNotaFiscal (se OK), dados de retorno e headers de limites.
    """
    url = f"{BASE_URL}/incluir.nota.xml.php"
    params = {"token": TOKEN, "formato": "json"}
    data = {
        "xml": xml_str,
        "lancarContas": "S" if lancar_contas else "N",
        "lancarEstoque": "S" if lancar_estoque else "N",
        "origemLancamentos": origem,
    }
    tentativa = 0
    waited = 0.0
    last = None
    while tentativa < max_retries:
        tentativa += 1
        try:
            resp = requests.post(url, params=params, data=data, timeout=60)
            x_limit_api = resp.headers.get("x-limit-api")
            x_remaining_api = resp.headers.get("x-remaining-api")
            try:
                body = resp.json()
            except Exception:
                body = {"erro": True, "mensagem": resp.text}
            retorno = body.get("retorno", {})
            status_txt = (retorno.get("status") or body.get("status") or "").upper()
            codigo_erro = retorno.get("codigo_erro")
            id_nota = retorno.get("idNotaFiscal")
            ok = status_txt == "OK" and not codigo_erro and bool(id_nota)
            last = {
                "ok": ok,
                "status_code": resp.status_code,
                "data": body,
                "text": resp.text[:2000],
                "tentativa": tentativa,
                "waited": waited,
                "x_limit_api": x_limit_api,
                "x_remaining_api": x_remaining_api,
                "idNotaFiscal": id_nota,
            }
            if ok:
                logger.info(f"Tiny incluir.nota.xml OK idNotaFiscal={id_nota} x-limit={x_limit_api} x-remain={x_remaining_api}")
                return last
            else:
                logger.warning(f"Tiny incluir.nota.xml falha status={status_txt} cod_erro={codigo_erro} http={resp.status_code} resp={str(body)[:500]}")
                is_rate = resp.status_code == 429 or (codigo_erro in (6, "6"))
                sleep_s = base_sleep * (2 ** (tentativa - 1)) if is_rate else base_sleep
                time.sleep(sleep_s)
                waited += sleep_s
        except requests.RequestException as e:
            logger.exception("Erro de rede ao incluir nota via XML: %s", e)
            time.sleep(base_sleep)
            waited += base_sleep
    return last or {"ok": False, "tentativa": tentativa, "waited": waited}

def buscar_nota_por_chave(chave: str) -> Dict[str, Any]:
    """
    Busca uma nota fiscal no Tiny pela chave de acesso.
    Retorna o ID da nota se encontrada.
    """
    url = f"{BASE_URL}/notas.fiscais.pesquisa.php"
    params = {"token": TOKEN, "formato": "json", "chaveAcesso": chave}
    try:
        resp = requests.post(url, params=params, timeout=60)
        data = resp.json() if resp.status_code == 200 else {}
        retorno = data.get('retorno', {})
        if retorno.get('status') == 'OK':
            notas = retorno.get('notas_fiscais', [])
            if notas and len(notas) > 0:
                nota = notas[0].get('nota_fiscal', {})
                id_nota = nota.get('id')
                return {'ok': True, 'id': id_nota, 'data': nota}
        return {'ok': False, 'error': 'Nota não encontrada', 'data': data}
    except Exception as e:
        return {'ok': False, 'error': str(e)}

def nota_fiscal_lancar_estoque(id_nota: int, max_retries: int = 3, base_sleep: float = 1.0) -> Dict[str, Any]:
    """
    Lança estoque para uma Nota Fiscal já existente no Tiny.
    Endpoint: nota.fiscal.lancar.estoque.php
    """
    url = f"{get_base_url()}/nota.fiscal.lancar.estoque.php"
    params = { 'token': get_token(), 'id': id_nota }
    attempt = 0
    last_error = None
    headers = {}
    while attempt <= max_retries:
        try:
            resp = requests.post(url, data=params, timeout=60)
            headers = dict(resp.headers)
            text = resp.text
            status_code = resp.status_code
            data = {}
            try:
                data = resp.json()
            except Exception:
                pass
            if status_code == 200 and data.get('retorno', {}).get('status') == 'OK':
                return { 'ok': True, 'status_code': status_code, 'text': text, 'data': data, 'headers': headers }
            # Rate limit / bloqueios
            codigo_erro = data.get('retorno', {}).get('codigo_erro')
            if status_code == 429 or codigo_erro == 6:
                sleep_time = base_sleep * (2 ** attempt)
                time.sleep(sleep_time)
                attempt += 1
                continue
            return { 'ok': False, 'status_code': status_code, 'text': text, 'data': data, 'headers': headers }
        except Exception as e:
            last_error = str(e)
            time.sleep(base_sleep * (2 ** attempt))
            attempt += 1
    return { 'ok': False, 'status_code': None, 'text': last_error or '', 'data': {}, 'headers': headers }
