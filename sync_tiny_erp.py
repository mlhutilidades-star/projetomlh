"""
Script de sincronização Tiny ERP
Importa pedidos do Tiny ERP e alimenta o banco de dados local como Contas a Pagar
"""
import sys
from datetime import datetime, timedelta
from modules.tiny_api import listar_produtos, listar_pedidos
from modules.database import get_db, ContaPagar, add_or_update_regra, init_database
from modules.validation import normalize_cnpj, parse_valor
from modules.observability import get_metrics, track_duration
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@track_duration('sync_tiny_duration', labels={'source': 'tiny'})
def sync_pedidos_tiny(dias=30):
    """
    Sincroniza pedidos do Tiny ERP dos últimos N dias
    
    Args:
        dias: Quantidade de dias para buscar (padrão 30)
    
    Returns:
        Dict com estatísticas da sincronização
    """
    logger.info(f"🏢 Iniciando sincronização Tiny ERP - últimos {dias} dias")
    
    # Inicializar banco
    init_database()
    
    # Calcular datas
    data_final = datetime.now()
    data_inicial = data_final - timedelta(days=dias)
    data_inicial_str = data_inicial.strftime('%d/%m/%Y')
    data_final_str = data_final.strftime('%d/%m/%Y')
    
    logger.info(f"📅 Período: {data_inicial_str} a {data_final_str}")
    
    stats = {
        'pedidos_processados': 0,
        'contas_criadas': 0,
        'contas_duplicadas': 0,
        'erros': 0,
        'regras_criadas': 0
    }
    
    page = 1
    total_paginas = 1
    
    while page <= total_paginas:
        logger.info(f"📄 Processando página {page}/{total_paginas}...")
        
        # Buscar pedidos
        resp = listar_pedidos(page=page, data_inicial=data_inicial_str, data_final=data_final_str)
        
        if 'error' in resp:
            logger.error(f"❌ Erro ao buscar pedidos: {resp['error']}")
            stats['erros'] += 1
            break
        
        retorno = resp.get('retorno', {})
        pedidos = retorno.get('pedidos', [])
        total_paginas = retorno.get('numero_paginas', 1)
        
        if not pedidos:
            logger.info("ℹ️ Nenhum pedido encontrado")
            break
        
        logger.info(f"✅ {len(pedidos)} pedidos retornados")
        
        # Processar cada pedido
        db = get_db()
        try:
            for item in pedidos:
                pedido = item.get('pedido', {})
                stats['pedidos_processados'] += 1
                
                try:
                    # Extrair dados do pedido
                    numero = pedido.get('numero')
                    numero_ecommerce = pedido.get('numero_ecommerce', '')
                    data_pedido_str = pedido.get('data_pedido', '')
                    cliente = pedido.get('nome', '')
                    valor = float(pedido.get('valor', 0))
                    situacao = pedido.get('situacao', 'Pendente')
                    vendedor = pedido.get('nome_vendedor', '')
                    
                    # Parse data
                    if data_pedido_str:
                        try:
                            data_pedido = datetime.strptime(data_pedido_str, '%d/%m/%Y').date()
                        except:
                            data_pedido = datetime.now().date()
                    else:
                        data_pedido = datetime.now().date()
                    
                    # Verificar se já existe (evitar duplicatas por hash)
                    import hashlib
                    dedup_key = f"{numero}|{valor}|{data_pedido.isoformat()}"
                    dedup_hash = hashlib.sha256(dedup_key.encode()).hexdigest()[:16]
                    
                    existing = db.query(ContaPagar).filter(
                        ContaPagar.observacoes.like(f"%HASH:{dedup_hash}%")
                    ).first()
                    
                    if existing:
                        logger.debug(f"⚠️ Pedido Tiny #{numero} já existe (hash {dedup_hash})")
                        stats['contas_duplicadas'] += 1
                        get_metrics().counter_inc('tiny_duplicates_skipped', labels={'source': 'tiny'})
                        continue
                    
                    # Criar conta a pagar
                    nova_conta = ContaPagar(
                        mes=data_pedido.month,
                        vencimento=data_pedido,
                        fornecedor=cliente if cliente else f"Pedido Tiny #{numero}",
                        cnpj=None,  # Tiny pedidos não retornam CNPJ na listagem
                        categoria="Pedido Tiny ERP",
                        descricao=f"Pedido #{numero} - {numero_ecommerce} - Vendedor: {vendedor}".strip(),
                        valor=valor,
                        status=situacao if situacao else "Pendente",
                        linha_digitavel=None,
                        pdf_url=None,
                        observacoes=f"Importado do Tiny ERP em {datetime.now().strftime('%d/%m/%Y %H:%M:%S')} | HASH:{dedup_hash}"
                    )
                    
                    db.add(nova_conta)
                    stats['contas_criadas'] += 1
                    logger.debug(f"✅ Conta criada: {cliente} - R$ {valor:.2f}")
                    get_metrics().counter_inc('tiny_orders_imported', labels={'source': 'tiny'})
                    
                except Exception as e:
                    logger.error(f"❌ Erro ao processar pedido #{pedido.get('numero')}: {e}")
                    stats['erros'] += 1
                    get_metrics().counter_inc('tiny_errors', labels={'source': 'tiny'})
            
            db.commit()
            logger.info(f"💾 Página {page} processada e salva")
            
        except Exception as e:
            logger.error(f"❌ Erro ao processar página {page}: {e}")
            db.rollback()
            stats['erros'] += 1
        finally:
            db.close()
        
        page += 1
    
    # Resumo
    logger.info("\n" + "=" * 60)
    logger.info("📊 RESUMO DA SINCRONIZAÇÃO TINY ERP")
    logger.info("=" * 60)
    logger.info(f"Pedidos processados: {stats['pedidos_processados']}")
    logger.info(f"Contas criadas: {stats['contas_criadas']}")
    logger.info(f"Contas duplicadas (ignoradas): {stats['contas_duplicadas']}")
    logger.info(f"Erros: {stats['erros']}")
    logger.info("=" * 60 + "\n")
    
    return stats

if __name__ == "__main__":
    # Sincronizar últimos 30 dias
    dias = 30
    if len(sys.argv) > 1:
        try:
            dias = int(sys.argv[1])
        except:
            print("Uso: python sync_tiny_erp.py [dias]")
            sys.exit(1)
    
    stats = sync_pedidos_tiny(dias=dias)
    
    if stats['erros'] > 0:
        sys.exit(1)
    else:
        sys.exit(0)
