"""
Sincronização automática de dados financeiros da Shopee
Importa pedidos completos com todas as informações financeiras
"""
import logging
from datetime import datetime, timedelta
from .shopee_api import listar_pedidos, get_access_token
from .database import add_conta, get_all_contas, SessionLocal, Conta
import time

logger = logging.getLogger('sync_apis')

def get_shopee_order_details(order_sn_list):
    """
    Obtém detalhes completos de pedidos Shopee
    
    Args:
        order_sn_list: Lista de order_sn para buscar detalhes
    
    Returns:
        Lista de pedidos com detalhes completos
    """
    from . import config
    import requests
    import hmac
    import hashlib
    
    if not config.SHOPEE_ACCESS_TOKEN:
        logger.error("Access token não disponível")
        return []
    
    path = "/api/v2/order/get_order_detail"
    timestamp = int(time.time())
    
    # Gerar assinatura
    partner_id = str(config.SHOPEE_PARTNER_ID)
    partner_key = config.SHOPEE_PARTNER_KEY
    access_token = config.SHOPEE_ACCESS_TOKEN
    shop_id = str(config.SHOPEE_SHOP_ID)
    
    base_string = f"{partner_id}{path}{timestamp}{access_token}{shop_id}"
    sign = hmac.new(
        partner_key.encode('utf-8'),
        base_string.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    
    url = f"https://partner.shopeemobile.com{path}"
    params = {
        'partner_id': partner_id,
        'timestamp': timestamp,
        'sign': sign,
        'shop_id': shop_id,
        'access_token': access_token,
        'order_sn_list': ','.join(order_sn_list[:50]),  # Max 50 por vez
        'response_optional_fields': 'buyer_user_id,buyer_username,estimated_shipping_fee,actual_shipping_fee,note,item_list,pay_time,total_amount,invoice_data,buyer_cpf_id,income_details'
    }
    
    try:
        logger.debug(f'Shopee: buscando detalhes de {len(order_sn_list)} pedidos')
        r = requests.get(url, params=params, timeout=30)
        r.raise_for_status()
        
        data = r.json()
        if 'error' in data:
            logger.error(f'Shopee API error: {data["error"]}')
            return []
        
        orders = data.get('response', {}).get('order_list', [])
        logger.info(f'Shopee: {len(orders)} pedidos detalhados retornados')
        return orders
        
    except Exception as e:
        logger.error(f'Erro ao buscar detalhes Shopee: {e}', exc_info=True)
        return []


def sync_shopee_pedidos(dias_atras=15):
    """
    Importa pedidos da Shopee com informações financeiras completas
    
    Args:
        dias_atras: Quantos dias para trás buscar (máx 15 dias pela API)
    
    Returns:
        Dict com estatísticas de importação
    """
    logger.info(f"Iniciando sincronização Shopee (últimos {dias_atras} dias)")
    
    access_token = get_access_token()
    if not access_token:
        logger.error("Access token Shopee não disponível")
        return {
            'total_importados': 0,
            'total_erros': 1,
            'pedidos': [],
            'erro': 'OAuth não configurado'
        }
    
    # Timestamps (máximo 15 dias pela API Shopee)
    time_to = int(time.time())
    time_from = time_to - min(dias_atras, 15) * 24 * 3600
    
    total_importados = 0
    total_erros = 0
    pedidos_processados = []
    
    try:
        # 1. Buscar lista de pedidos
        resultado = listar_pedidos(time_from=time_from, time_to=time_to)
        
        if 'error' in resultado:
            logger.error(f"Erro ao buscar pedidos Shopee: {resultado['error']}")
            return {
                'total_importados': 0,
                'total_erros': 1,
                'pedidos': [],
                'erro': resultado['error']
            }
        
        order_list = resultado.get('order_list', [])
        logger.info(f"Shopee retornou {len(order_list)} pedidos para processar")
        
        if not order_list:
            return {
                'total_importados': 0,
                'total_erros': 0,
                'pedidos': [],
                'mensagem': 'Nenhum pedido no período'
            }
        
        # 2. Buscar detalhes dos pedidos (em lotes de 50)
        order_sn_list = [p['order_sn'] for p in order_list]
        
        all_details = []
        for i in range(0, len(order_sn_list), 50):
            batch = order_sn_list[i:i+50]
            details = get_shopee_order_details(batch)
            all_details.extend(details)
            time.sleep(0.5)  # Rate limiting
        
        # 3. Processar cada pedido e criar registro financeiro
        for pedido in all_details:
            try:
                order_sn = pedido.get('order_sn', '')
                order_status = pedido.get('order_status', '')
                
                # Calcular valores financeiros
                total_amount = float(pedido.get('total_amount', 0))  # Total pago pelo comprador
                actual_shipping_fee = float(pedido.get('actual_shipping_fee', 0))
                
                # Receita líquida (após taxas Shopee)
                # A API retorna income_details com valores detalhados
                income_details = pedido.get('income_details', {})
                
                # Valores principais
                receita_bruta = total_amount
                taxa_comissao = float(income_details.get('commission_fee', 0))
                taxa_servico = float(income_details.get('service_fee', 0))
                taxa_transacao = float(income_details.get('transaction_fee', 0))
                custo_frete = actual_shipping_fee
                
                # Receita líquida = Total - Taxas
                receita_liquida = receita_bruta - (taxa_comissao + taxa_servico + taxa_transacao)
                
                # Data do pagamento
                pay_time = pedido.get('pay_time')
                if pay_time:
                    data_pagamento = datetime.fromtimestamp(pay_time)
                    vencimento = data_pagamento.strftime('%Y-%m-%d')
                else:
                    vencimento = datetime.now().strftime('%Y-%m-%d')
                
                # Nome do comprador
                comprador = pedido.get('buyer_username', 'Comprador Shopee')
                
                # Itens do pedido
                item_list = pedido.get('item_list', [])
                qtd_itens = sum(item.get('model_quantity_purchased', 0) for item in item_list)
                
                # Criar registro financeiro
                observacao = f"""Pedido Shopee #{order_sn}
Status: {order_status}
Comprador: {comprador}
Itens: {qtd_itens}
Receita Bruta: R$ {receita_bruta:.2f}
Taxa Comissão: R$ {taxa_comissao:.2f}
Taxa Serviço: R$ {taxa_servico:.2f}
Taxa Transação: R$ {taxa_transacao:.2f}
Frete: R$ {custo_frete:.2f}
Receita Líquida: R$ {receita_liquida:.2f}"""
                
                conta_data = {
                    'fornecedor': f'Shopee - {comprador}',
                    'cnpj': '',
                    'valor': receita_liquida,  # Usar receita líquida
                    'vencimento': vencimento,
                    'categoria': 'Receita Shopee',
                    'status': 'Pago' if order_status in ['COMPLETED', 'SHIPPED'] else 'Pendente',
                    'observacao': observacao,
                    'linha_digitavel': order_sn,
                    'descricao': f'{qtd_itens} itens'
                }
                
                conta_id = add_conta(**conta_data)
                if conta_id:
                    total_importados += 1
                    pedidos_processados.append(f"Pedido {order_sn} - R$ {receita_liquida:.2f}")
                    logger.info(f"Pedido Shopee {order_sn} importado (ID: {conta_id}, Líquido: R$ {receita_liquida:.2f})")
                else:
                    total_erros += 1
                    
            except Exception as e:
                logger.error(f"Erro ao processar pedido Shopee {order_sn}: {e}")
                total_erros += 1
        
    except Exception as e:
        logger.error(f"Erro na sincronização Shopee: {e}", exc_info=True)
        total_erros += 1
    
    logger.info(f"Sincronização Shopee concluída: {total_importados} importados, {total_erros} erros")
    
    return {
        'total_importados': total_importados,
        'total_erros': total_erros,
        'pedidos': pedidos_processados
    }


def get_sync_stats():
    """
    Retorna estatísticas sobre dados sincronizados
    
    Returns:
        Dict com estatísticas
    """
    session = SessionLocal()
    try:
        total_contas = session.query(Conta).count()
        contas_shopee = session.query(Conta).filter(Conta.categoria.like('%Shopee%')).count()
        receitas_shopee = session.query(Conta).filter(Conta.categoria.like('%Shopee%')).all()
        
        # Calcular totais financeiros
        total_receita_shopee = sum(c.valor for c in receitas_shopee if c.valor > 0)
        
        return {
            'total_contas': total_contas,
            'contas_shopee': contas_shopee,
            'outras': total_contas - contas_shopee,
            'receita_shopee_total': total_receita_shopee
        }
    finally:
        session.close()
