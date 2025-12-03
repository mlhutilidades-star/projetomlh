import time, hmac, hashlib, requests, json, os, re
import logging
from . import config

logger = logging.getLogger('shopee_api')
HOST = "https://partner.shopeemobile.com"

def _generate_sign(path, timestamp, access_token="", shop_id=""):
    """
    Generate HMAC-SHA256 signature for Shopee API v2
    
    For shop-level APIs (with access_token):
        base_string = partner_id + path + timestamp + access_token + shop_id
    
    For partner-level APIs (without access_token):
        base_string = partner_id + path + timestamp
    
    Args:
        path: API path (e.g., /api/v2/order/get_order_list)
        timestamp: Unix timestamp in seconds
        access_token: Shop access token (optional)
        shop_id: Shop ID (optional)
    
    Returns:
        HMAC-SHA256 hex digest
    """
    partner_id = str(config.SHOPEE_PARTNER_ID)
    partner_key = config.SHOPEE_PARTNER_KEY
    
    if access_token and shop_id:
        # Shop-level API
        base_string = f"{partner_id}{path}{timestamp}{access_token}{shop_id}"
    else:
        # Partner-level API
        base_string = f"{partner_id}{path}{timestamp}"
    
    logger.debug(f"Base string for signing: {base_string}")
    
    sign = hmac.new(
        partner_key.encode('utf-8'),
        base_string.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    
    return sign


def get_access_token():
    """
    Obtém access token para autenticação shop-level
    
    NOTA: Para usar shop-level APIs, você precisa primeiro:
    1. Registrar app no Shopee Partner Portal
    2. Obter autorização da loja (OAuth flow)
    3. Trocar code por access_token
    
    Por enquanto, retorna o token do .env se existir
    """
    access_token = config.SHOPEE_ACCESS_TOKEN
    if access_token:
        return access_token
    
    # TODO: Implementar OAuth flow completo se necessário
    # Por enquanto, retorna None se não tiver token configurado
    return None


def _update_env_tokens(access_token: str, refresh_token: str | None = None):
    """Atualiza tokens no arquivo .env local e em config em runtime."""
    env_path = os.path.join(os.getcwd(), '.env')
    try:
        lines = []
        if os.path.exists(env_path):
            with open(env_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
        
        def set_line(key: str, value: str):
            nonlocal lines
            key_eq = f"{key}="
            for i, line in enumerate(lines):
                if line.startswith(key_eq) or line.startswith(f"# {key}="):
                    lines[i] = f"{key}={value}\n"
                    return
            lines.append(f"{key}={value}\n")
        
        set_line('SHOPEE_ACCESS_TOKEN', access_token)
        if refresh_token is not None:
            set_line('SHOPEE_REFRESH_TOKEN', refresh_token)
        
        with open(env_path, 'w', encoding='utf-8') as f:
            f.writelines(lines)
        
        # Atualiza em runtime para esta sessão
        config.SHOPEE_ACCESS_TOKEN = access_token
        os.environ['SHOPEE_ACCESS_TOKEN'] = access_token
        if refresh_token is not None:
            os.environ['SHOPEE_REFRESH_TOKEN'] = refresh_token
        
        logger.info('Tokens Shopee atualizados no .env')
        return True
    except Exception as e:
        logger.error(f'Falha ao atualizar .env com tokens: {e}', exc_info=True)
        return False


def _refresh_access_token():
    """Atualiza access_token usando refresh_token da Shopee API v2.
    Retorna novo access_token em caso de sucesso, senão None.
    """
    partner_id = str(config.SHOPEE_PARTNER_ID)
    partner_key = config.SHOPEE_PARTNER_KEY
    shop_id = str(config.SHOPEE_SHOP_ID)
    refresh_token = os.getenv('SHOPEE_REFRESH_TOKEN', '')
    if not (partner_id and partner_key and shop_id and refresh_token):
        logger.warning('Parâmetros insuficientes para refresh do access_token')
        return None
    
    path = "/api/v2/auth/access_token/get"
    timestamp = int(time.time())
    # Refresh é partner-level (sem access_token na base string)
    base_string = f"{partner_id}{path}{timestamp}"
    sign = hmac.new(partner_key.encode('utf-8'), base_string.encode('utf-8'), hashlib.sha256).hexdigest()
    
    url = f"{HOST}{path}?partner_id={partner_id}&timestamp={timestamp}&sign={sign}"
    body = {
        "shop_id": int(shop_id),
        "refresh_token": refresh_token,
        "partner_id": int(partner_id)
    }
    try:
        r = requests.post(url, json=body, timeout=30)
        data = r.json() if r.headers.get('content-type','').startswith('application/json') else {"raw": r.text}
        if r.status_code != 200 or (isinstance(data, dict) and data.get('error')):
            logger.error(f"Falha no refresh token: HTTP {r.status_code} - {data}")
            return None
        new_access = data.get('access_token')
        new_refresh = data.get('refresh_token') or refresh_token
        if new_access:
            _update_env_tokens(new_access, new_refresh)
            return new_access
    except Exception as e:
        logger.error(f'Erro ao atualizar access_token: {e}', exc_info=True)
    return None


def listar_produtos(page_size=20, offset=0):
    """
    Lista produtos da loja (requer autenticação shop-level)
    
    IMPORTANTE: Shopee API v2 requer access_token para APIs de loja
    Esta função está preparada mas precisa de OAuth configurado
    
    Args:
        page_size: Quantidade de produtos por página
        offset: Offset para paginação
    
    Returns:
        Dict com produtos ou erro
    """
    if not (config.SHOPEE_PARTNER_ID and config.SHOPEE_PARTNER_KEY and config.SHOPEE_SHOP_ID):
        logger.warning('Shopee credentials not configured')
        return {'error': 'Credenciais não configuradas', 'items': []}
    
    access_token = get_access_token()
    if not access_token:
        logger.warning('Shopee access_token not available. OAuth flow needed.')
        return {
            'error': 'Access token não configurado. Configure OAuth no Shopee Partner Portal.',
            'items': [],
            'info': 'Shopee API v2 requer OAuth para acessar dados da loja'
        }
    
    path = "/api/v2/product/get_item_list"
    timestamp = int(time.time())
    sign = _generate_sign(path, timestamp, access_token, config.SHOPEE_SHOP_ID)
    
    url = f"{HOST}{path}"
    params = {
        'partner_id': config.SHOPEE_PARTNER_ID,
        'timestamp': timestamp,
        'sign': sign,
        'shop_id': config.SHOPEE_SHOP_ID,
        'access_token': access_token,
        'page_size': page_size,
        'offset': offset
    }
    
    try:
        logger.debug(f'Shopee API: listing products (page_size={page_size}, offset={offset})')
        def do_request(p):
            r_local = requests.get(url, params=p, timeout=30)
            try:
                data_local = r_local.json()
            except Exception:
                data_local = {"raw": r_local.text}
            return r_local.status_code, data_local

        status, data = do_request(params)
        if status != 200 or (isinstance(data, dict) and data.get('error')):
            # Tentar refresh automático como em pedidos
            logger.warning(f"Produto: possível erro de auth ou HTTP {status}. Tentando refresh...")
            new_token = _refresh_access_token()
            if new_token:
                timestamp2 = int(time.time())
                sign2 = _generate_sign(path, timestamp2, new_token, config.SHOPEE_SHOP_ID)
                params.update({'timestamp': timestamp2, 'sign': sign2, 'access_token': new_token})
                status, data = do_request(params)

        if isinstance(data, dict) and data.get('error') and not data.get('response'):
            logger.error(f"Shopee API error: {data.get('error')} :: {data}")
            return {'error': data.get('error'), 'items': []}

        items = (data or {}).get('response', {}).get('item', [])
        logger.info(f'Shopee API: {len(items)} products returned')
        return {'items': items, 'response': (data or {}).get('response', {})}
    
    except Exception as e:
        logger.error(f'Erro ao listar produtos Shopee: {e}', exc_info=True)
        return {'error': str(e), 'items': []}


def listar_pedidos(time_from=None, time_to=None, cursor: str = '', page_size: int = 50, dias: int | None = None):
    """
    Lista pedidos da Shopee (requer autenticação shop-level)
    
    IMPORTANTE: Shopee API v2 mudou completamente em 2023:
    - Todas as APIs de loja (shop-level) requerem OAuth 2.0
    - Não é mais possível usar apenas Partner ID/Key
    - É necessário: Partner ID, Partner Key, Shop ID, e ACCESS_TOKEN
    
    Args:
        time_from: Timestamp inicial (unix epoch)
        time_to: Timestamp final (unix epoch)
    
    Returns:
        Dict com pedidos ou erro (com instruções de configuração)
    """
    if not (config.SHOPEE_PARTNER_ID and config.SHOPEE_PARTNER_KEY and config.SHOPEE_SHOP_ID):
        logger.warning('Shopee credentials not configured')
        return {'error': 'Credenciais não configuradas', 'order_list': []}
    
    # Shopee API v2 REQUER access_token para shop-level APIs
    access_token = get_access_token()
    if not access_token:
        logger.warning('Shopee access_token not available')
        return {
            'error': 'OAuth não configurado',
            'order_list': [],
            'mensagem': 'Shopee API v2 requer OAuth 2.0 para acessar pedidos',
            'instrucoes': [
                '1. Acesse Shopee Partner Portal (https://partner.shopeemobile.com)',
                '2. Crie/configure sua aplicação',
                '3. Obtenha autorização da loja (OAuth flow)',
                '4. Configure SHOPEE_ACCESS_TOKEN no .env',
                '5. Implemente refresh token automático'
            ],
            'documentacao': 'https://open.shopee.com/documents/v2/v2.order.get_order_list'
        }
    
    path = "/api/v2/order/get_order_list"
    timestamp = int(time.time())
    
    # Shopee exige time_range_field + time_from/time_to
    if dias and isinstance(dias, int) and dias > 0:
        # usa intervalo baseado em dias informado, respeitando máximo 15
        span_days = min(int(dias), 15)
        time_to = timestamp
        time_from = timestamp - (span_days * 24 * 3600)
    elif not time_from or not time_to:
        # Últimos 15 dias (máximo permitido pela API)
        time_to = timestamp
        time_from = timestamp - (15 * 24 * 3600)
    
    # Gerar assinatura com access_token
    sign = _generate_sign(path, timestamp, access_token, config.SHOPEE_SHOP_ID)
    
    url = f"{HOST}{path}"
    params = {
        'partner_id': config.SHOPEE_PARTNER_ID,
        'timestamp': timestamp,
        'sign': sign,
        'shop_id': config.SHOPEE_SHOP_ID,
        'access_token': access_token,
        'time_range_field': 'create_time',
        'time_from': time_from,
        'time_to': time_to,
        'page_size': page_size,
        'cursor': cursor or ''
    }
    
    try:
        def do_request(params_local):
            r_local = requests.get(url, params=params_local, timeout=30)
            # Não usar raise_for_status para capturar corpo em erros
            try:
                data_local = r_local.json()
            except Exception:
                data_local = {"raw": r_local.text}
            return r_local.status_code, data_local

        logger.debug(f'Shopee API: listing orders from {time_from} to {time_to}')
        status, data = do_request(params)

        def is_auth_error(payload):
            if not isinstance(payload, dict):
                return False
            err = (payload.get('error') or '').lower()
            msg = (payload.get('message') or '').lower()
            return (
                'access' in err or 'auth' in err or 'unauth' in err or
                'token' in err or 'access token' in msg or 'expired' in msg
            )

        if status != 200 or ('error' in data and is_auth_error(data)):
            logger.warning('Possível expiração/invalidade do access_token. Tentando refresh e reprocessar...')
            new_token = _refresh_access_token()
            if new_token:
                # recomputar assinatura e repetir
                timestamp2 = int(time.time())
                sign2 = _generate_sign(path, timestamp2, new_token, config.SHOPEE_SHOP_ID)
                params.update({
                    'timestamp': timestamp2,
                    'sign': sign2,
                    'access_token': new_token
                })
                status, data = do_request(params)

        if isinstance(data, dict) and 'error' in data and not data.get('response'):
            logger.error(f"Shopee API error: {data.get('error')} :: {data}")
            return {'error': data.get('error'), 'order_list': [], 'response': data}

        response = data.get('response', {}) if isinstance(data, dict) else {}
        orders = response.get('order_list', [])
        total_count = response.get('total_count') or len(orders)

        logger.info(f'Shopee API: {len(orders)} orders returned (total_count={total_count}) cursor={cursor}')

        return {
            'order_list': orders,
            'more': response.get('more', False),
            'next_cursor': response.get('next_cursor', ''),
            'total_count': total_count,
            'time_from': time_from,
            'time_to': time_to
        }
    
    except requests.exceptions.Timeout:
        logger.error('Shopee API timeout')
        return {'error': 'Timeout na requisição', 'order_list': []}
    except requests.exceptions.RequestException as e:
        logger.error(f'Shopee API request error: {e}', exc_info=True)
        return {'error': str(e), 'order_list': []}
    except Exception as e:
        logger.error(f'Unexpected error: {e}', exc_info=True)
        return {'error': 'Erro inesperado', 'order_list': []}


def obter_detalhe_pedido(order_sn: str):
    """Obtém detalhes de um pedido (valores detalhados) pela Shopee API v2.

    Retorna dict com 'order' ou {'error': ...}.
    """
    if not (config.SHOPEE_PARTNER_ID and config.SHOPEE_PARTNER_KEY and config.SHOPEE_SHOP_ID):
        logger.warning('Shopee credentials not configured')
        return {'error': 'Credenciais não configuradas'}

    access_token = get_access_token()
    if not access_token:
        logger.warning('Shopee access_token not available')
        return {'error': 'OAuth não configurado'}

    path = "/api/v2/order/get_order_detail"
    timestamp = int(time.time())
    sign = _generate_sign(path, timestamp, access_token, config.SHOPEE_SHOP_ID)
    url = f"{HOST}{path}"
    params = {
        'partner_id': config.SHOPEE_PARTNER_ID,
        'timestamp': timestamp,
        'sign': sign,
        'shop_id': config.SHOPEE_SHOP_ID,
        'access_token': access_token,
        'order_sn_list': order_sn,
           'response_optional_fields': 'buyer_username,recipient_address,item_list,escrow_detail,buyer_user_id,buyer_username,estimated_shipping_fee,recipient_address,actual_shipping_fee,goods_to_declare,note,note_update_time,item_list,pay_time,dropshipper,dropshipper_phone,split_up,buyer_cancel_reason,cancel_by,cancel_reason,actual_shipping_fee_confirmed,buyer_cpf,fulfillment_flag,pickup_done_time,package_list,shipping_carrier,payment_method,total_amount,buyer_username,invoice_data,checkout_shipping_carrier,reverse_shipping_fee,order_chargeable_weight_gram,edt,prescription_images,prescription_check_status'
    }

    try:
        r = requests.get(url, params=params, timeout=30)
        try:
            data = r.json()
        except Exception:
            data = {'raw': r.text}
        if r.status_code != 200 or (isinstance(data, dict) and data.get('error') and not data.get('response')):
            logger.error(f"Shopee detalhe pedido erro: HTTP {r.status_code} - {data}")
            return {'error': data.get('error') or f'HTTP {r.status_code}'}
        response = (data or {}).get('response', {})
        orders = response.get('order_list', []) or response.get('order', [])
        # A API pode retornar 'order_list' com itens contendo 'price_info' e 'escrow_amount'
        if isinstance(orders, list) and orders:
            return {'order': orders[0]}
        return {'order': response.get('order')}
    except Exception as e:
        logger.error(f'Erro ao obter detalhe do pedido {order_sn}: {e}', exc_info=True)
        return {'error': str(e)}
