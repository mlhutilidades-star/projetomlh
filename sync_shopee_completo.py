"""Sincronização COMPLETA de pedidos Shopee com RECEITAS e DESPESAS separadas

Este script importa cada pedido da Shopee criando múltiplos registros:
1. RECEITA: Valor total do pedido (total_amount)
2. DESPESAS DE VENDA:
   - Taxa de Comissão Shopee
   - Taxa de Serviço Shopee
   - Frete (quando aplicável)
   
Isso permite calcular corretamente a margem de contribuição.
"""
from datetime import datetime, timedelta
import time
import sys
import logging
from modules.database import init_database, get_db, ContaPagar
from modules.shopee_api import listar_pedidos, obter_detalhe_pedido
from modules.tiny_api import obter_produto_por_sku

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger('sync_shopee_completo')

MAX_WINDOW_DAYS = 15
MAX_PAGES_PER_WINDOW = 200

def _parse_date(ts: int):
    try:
        return datetime.fromtimestamp(int(ts)).date()
    except Exception:
        return datetime.now().date()

def _import_order_completo(order_sn: str, db):
    """Importa um pedido completo com receitas e despesas separadas."""
    try:
        # Buscar detalhes completos
        det = obter_detalhe_pedido(order_sn)
        order = det.get('order', {})
        
        if not order or 'error' in det:
            logger.warning(f"⚠️  Pedido {order_sn}: sem detalhes ou erro")
            return 0
        
        # Dados básicos
        create_time = order.get('create_time')
        buyer_username = order.get('buyer_username', '')
        order_status = order.get('order_status', '')
        vencimento = _parse_date(create_time)
        
        # Valores principais
        total_amount = float(order.get('total_amount', 0))
        actual_shipping_fee = float(order.get('actual_shipping_fee', 0))
        estimated_shipping_fee = float(order.get('estimated_shipping_fee', 0))
        
        # Dados da nota fiscal (quando disponível)
        invoice_data = order.get('invoice_data', {})
        invoice_total = float(invoice_data.get('total_value', 0)) if invoice_data else 0
        invoice_products = float(invoice_data.get('products_total_value', 0)) if invoice_data else 0
        
        # Itens do pedido
        item_list = order.get('item_list', [])
        items_descricao = []
        custo_total_itens = 0.0
        for item in item_list:
            nome = item.get('item_name', '')[:50]
            qtd = item.get('model_quantity_purchased', 1)
            preco = float(item.get('model_discounted_price', 0))
            items_descricao.append(f"{qtd}x {nome} (R${preco:.2f})")
            # Obter SKU para buscar custo no Tiny
            sku = item.get('model_sku') or item.get('item_sku') or ''
            if sku:
                tin = obter_produto_por_sku(sku)
                preco_custo = tin.get('preco_custo', 0.0) if isinstance(tin, dict) else 0.0
                if preco_custo and qtd:
                    custo_total_itens += float(preco_custo) * float(qtd)
        
        produtos_desc = " | ".join(items_descricao[:3])  # Máximo 3 itens
        
        # Verificar se já foi importado
        dup = db.query(ContaPagar).filter(
            ContaPagar.observacoes.like(f"%SN:{order_sn}%")
        ).first()
        if dup:
            logger.info(f"⏭️  Pedido {order_sn}: já importado")
            return 0
        
        registros_criados = 0
        
        # 1. RECEITA - Valor total do pedido
        if total_amount > 0:
            receita = ContaPagar(
                mes=vencimento.month,
                vencimento=vencimento,
                fornecedor=f"Shopee - {buyer_username}" if buyer_username else "Shopee",
                cnpj=None,
                categoria="Receita Shopee",
                descricao=f"Pedido {order_sn} - {produtos_desc}",
                valor=total_amount,
                status=order_status,
                observacoes=f"SN:{order_sn} | buyer:{buyer_username} | status:{order_status} | payment:{order.get('payment_method', 'N/A')}"
            )
            db.add(receita)
            registros_criados += 1
            logger.info(f"  💰 Receita: R$ {total_amount:.2f}")
        
        # 2. DESPESA - Taxa de Comissão Shopee
        # Calcular como diferença entre total da NF e valor dos produtos
        if invoice_total > 0 and invoice_products > 0:
            taxa_comissao = invoice_total - invoice_products
            if taxa_comissao > 0:
                desp_comissao = ContaPagar(
                    mes=vencimento.month,
                    vencimento=vencimento,
                    fornecedor="Shopee",
                    cnpj=None,
                    categoria="Despesa Venda - Taxa Comissão Shopee",
                    descricao=f"Taxa Comissão - Pedido {order_sn}",
                    valor=taxa_comissao,
                    status=order_status,
                    observacoes=f"SN:{order_sn} | NF:{invoice_data.get('number', 'N/A')} | Base: R${invoice_products:.2f}"
                )
                db.add(desp_comissao)
                registros_criados += 1
                logger.info(f"  📉 Taxa Comissão: R$ {taxa_comissao:.2f}")
        
        # 3. DESPESA - Frete (quando o vendedor paga)
        # Se actual_shipping_fee > 0, é custo do vendedor
        if actual_shipping_fee > 0:
            desp_frete = ContaPagar(
                mes=vencimento.month,
                vencimento=vencimento,
                fornecedor="Shopee",
                cnpj=None,
                categoria="Despesa Venda - Frete Shopee",
                descricao=f"Frete - Pedido {order_sn}",
                valor=actual_shipping_fee,
                status=order_status,
                observacoes=f"SN:{order_sn} | Carrier:{order.get('shipping_carrier', 'N/A')}"
            )
            db.add(desp_frete)
            registros_criados += 1
            logger.info(f"  🚚 Frete: R$ {actual_shipping_fee:.2f}")
        
        # 4. DESPESA - Custo do Produto (Tiny)
        if custo_total_itens > 0:
            desp_custo = ContaPagar(
                mes=vencimento.month,
                vencimento=vencimento,
                fornecedor="Tiny ERP",
                cnpj=None,
                categoria="Despesa Venda - Custo Produto (Tiny)",
                descricao=f"Custo Produtos - Pedido {order_sn}",
                valor=custo_total_itens,
                status=order_status,
                observacoes=f"SN:{order_sn} | Itens: {len(item_list)}"
            )
            db.add(desp_custo)
            registros_criados += 1
            logger.info(f"  🧾 Custo Produtos (Tiny): R$ {custo_total_itens:.2f}")

        # Commit
        db.commit()
        logger.info(f"✅ Pedido {order_sn}: {registros_criados} registros criados")
        return registros_criados
        
    except Exception as e:
        logger.error(f"❌ Erro ao processar pedido {order_sn}: {e}", exc_info=True)
        return 0

def sync_shopee_completo(dias: int = 30):
    """Sincroniza pedidos Shopee dos últimos N dias com receitas e despesas."""
    init_database()
    
    logger.info(f"🚀 Iniciando sincronização Shopee - últimos {dias} dias")
    logger.info("="*80)
    
    now = int(time.time())
    start_ts = now - (dias * 86400)
    
    total_pedidos = 0
    total_registros = 0
    
    # Dividir em janelas de 15 dias
    windows = []
    current_start = start_ts
    while current_start < now:
        current_end = min(current_start + (MAX_WINDOW_DAYS * 86400), now)
        windows.append((current_start, current_end))
        current_start = current_end
    
    logger.info(f"📅 Dividido em {len(windows)} janelas de até {MAX_WINDOW_DAYS} dias")
    
    for idx, (ts_from, ts_to) in enumerate(windows, 1):
        data_from = datetime.fromtimestamp(ts_from).strftime('%d/%m/%Y')
        data_to = datetime.fromtimestamp(ts_to).strftime('%d/%m/%Y')
        logger.info(f"\n[Janela {idx}/{len(windows)}] {data_from} → {data_to}")
        logger.info("-"*80)
        
        cursor = ''
        page_num = 0
        last_cursor = None
        
        while page_num < MAX_PAGES_PER_WINDOW:
            page_num += 1
            
            try:
                resp = listar_pedidos(
                    time_from=ts_from,
                    time_to=ts_to,
                    cursor=cursor,
                    page_size=50
                )
                
                if 'error' in resp:
                    logger.error(f"Erro na API: {resp.get('error')}")
                    break
                
                # A API retorna order_list direto no response
                orders = resp.get('order_list', [])
                next_cursor = resp.get('next_cursor', '')
                more = resp.get('more', False)
                
                if not orders:
                    logger.info(f"  Página {page_num}: sem pedidos")
                    break
                
                logger.info(f"  Página {page_num}: {len(orders)} pedidos encontrados")
                
                # Processar cada pedido
                db = get_db()
                try:
                    for order in orders:
                        order_sn = order.get('order_sn')
                        if order_sn:
                            registros = _import_order_completo(order_sn, db)
                            if registros > 0:
                                total_pedidos += 1
                                total_registros += registros
                finally:
                    db.close()
                
                # Verificar cursor repetido (proteção contra loop)
                if next_cursor and next_cursor == last_cursor:
                    logger.warning(f"⚠️  Cursor repetido detectado. Encerrando janela.")
                    break
                
                last_cursor = next_cursor
                
                # Próxima página
                if more and next_cursor:
                    cursor = next_cursor
                    time.sleep(0.5)  # Rate limiting
                else:
                    break
                    
            except Exception as e:
                logger.error(f"Erro na página {page_num}: {e}", exc_info=True)
                break
    
    logger.info("\n" + "="*80)
    logger.info(f"✅ Sincronização concluída!")
    logger.info(f"   Total de pedidos processados: {total_pedidos}")
    logger.info(f"   Total de registros criados: {total_registros}")
    logger.info("="*80)
    
    return total_pedidos, total_registros

if __name__ == '__main__':
    dias = int(sys.argv[1]) if len(sys.argv) > 1 else 30
    sync_shopee_completo(dias)
