"""Auditoria de SKUs sem custo (preco_custo) no Tiny ERP

Percorre pedidos Shopee dos últimos N dias e lista SKUs cujo preco_custo
retornado pelo Tiny é 0 ou ausente.

Saídas:
- Impressão em tabela no terminal
- Arquivo CSV: missing_custos.csv
- Arquivo JSON: missing_custos.json

Uso:
    python audit_custos_tiny.py 60   # últimos 60 dias
"""
from __future__ import annotations
import sys, time, csv, json
from datetime import datetime
from collections import defaultdict
from modules.shopee_api import listar_pedidos, obter_detalhe_pedido
from modules.tiny_api import obter_produto_por_sku

MAX_WINDOW_DAYS = 15
PAGE_SIZE = 50
MAX_PAGES_PER_WINDOW = 60  # proteção contra loops
MAX_ORDERS_TOTAL = 5000    # proteção: não processar mais que X pedidos

def _split_windows(dias: int):
    now = int(time.time())
    start = now - dias * 86400
    windows = []
    cur = start
    while cur < now:
        end = min(cur + MAX_WINDOW_DAYS * 86400, now)
        windows.append((cur, end))
        cur = end
    return windows

def auditar_skus_sem_custo(dias: int = 30, quick: bool = False):
    windows = _split_windows(dias)
    cache_tiny = {}
    missing = {}
    stats = defaultdict(lambda: {"sku": None, "nome": None, "qty": 0, "orders": set(), "last_order": None})
    total_orders = 0
    processed_orders = 0

    for w_idx, (ts_from, ts_to) in enumerate(windows, 1):
        print(f"[Janela {w_idx}/{len(windows)}] {datetime.fromtimestamp(ts_from).strftime('%d/%m/%Y')} → {datetime.fromtimestamp(ts_to).strftime('%d/%m/%Y')}")
        cursor = ''
        page = 0
        last_cursor = None
        while page < MAX_PAGES_PER_WINDOW:
            page += 1
            if quick and page > 5:
                # modo rápido: limita 5 páginas por janela
                break
            resp = listar_pedidos(time_from=ts_from, time_to=ts_to, cursor=cursor, page_size=PAGE_SIZE)
            if 'error' in resp:
                print(f"Erro API Shopee: {resp.get('error')}")
                break
            orders = resp.get('order_list', [])
            more = resp.get('more', False)
            next_cursor = resp.get('next_cursor', '')
            if not orders:
                print(f"  Página {page}: sem pedidos")
                break
            print(f"  Página {page}: {len(orders)} pedidos")
            total_orders += len(orders)
            for od in orders:
                order_sn = od.get('order_sn')
                if not order_sn:
                    continue
                processed_orders += 1
                if processed_orders % 50 == 0:
                    print(f"    .. {processed_orders} pedidos processados (acumulado)")
                if processed_orders >= MAX_ORDERS_TOTAL:
                    print(f"⚠️  Limite de {MAX_ORDERS_TOTAL} pedidos atingido. Encerrando auditoria antecipadamente.")
                    break
                det = obter_detalhe_pedido(order_sn)
                order = det.get('order', {})
                item_list = order.get('item_list', [])
                for item in item_list:
                    sku = item.get('model_sku') or item.get('item_sku') or ''
                    if not sku:
                        continue
                    if sku not in cache_tiny:
                        tin = obter_produto_por_sku(sku)
                        cache_tiny[sku] = tin if isinstance(tin, dict) else {}
                    tin = cache_tiny[sku]
                    preco_custo = tin.get('preco_custo', 0.0) or 0.0
                    if preco_custo <= 0:
                        nome = (tin.get('nome') or item.get('item_name') or '').strip()[:80]
                        qty = item.get('model_quantity_purchased', 1) or 1
                        st = stats[sku]
                        st['sku'] = sku
                        st['nome'] = nome or 'SEM NOME'
                        st['qty'] += int(qty)
                        st['orders'].add(order_sn)
                        st['last_order'] = order_sn
            if more and next_cursor and next_cursor != last_cursor:
                cursor = next_cursor
                last_cursor = next_cursor
                time.sleep(0.2)
            else:
                break
        if processed_orders >= MAX_ORDERS_TOTAL:
            break
    # Construir lista final
    rows = []
    for sku, data in stats.items():
        rows.append({
            'sku': sku,
            'nome': data['nome'],
            'qtd_total_sem_custo': data['qty'],
            'pedidos_distintos': len(data['orders']),
            'ultimo_pedido': data['last_order']
        })
    rows.sort(key=lambda r: r['qtd_total_sem_custo'], reverse=True)

    # Salvar CSV / JSON
    if rows:
        with open('missing_custos.csv', 'w', newline='', encoding='utf-8') as f:
            w = csv.DictWriter(f, fieldnames=rows[0].keys())
            w.writeheader()
            w.writerows(rows)
        with open('missing_custos.json', 'w', encoding='utf-8') as f:
            json.dump({'dias': dias, 'total_orders': total_orders, 'skus_sem_custo': rows}, f, ensure_ascii=False, indent=2)
    print(f"\n=== AUDITORIA COGS (últimos {dias} dias) ===")
    print(f"Pedidos varridos: {processed_orders} (linhas API: {total_orders})")
    print(f"SKUs sem custo únicos: {len(rows)}")
    print()
    if not rows:
        print("Todos os SKUs têm custo > 0.")
        return rows
    header = f"{'SKU':<18} {'QTD':>5} {'PEDIDOS':>7} {'ULTIMO_PEDIDO':<18} NOME"
    print(header)
    print('-'*len(header))
    for r in rows[:120]:  # limitar impressão
        print(f"{r['sku']:<18} {r['qtd_total_sem_custo']:>5} {r['pedidos_distintos']:>7} {r['ultimo_pedido']:<18} {r['nome']}")
    if len(rows) > 120:
        print(f"... (+{len(rows)-120} SKUs adicionais)" )
    print("\nArquivos gerados: missing_custos.csv, missing_custos.json")
    return rows

if __name__ == '__main__':
    dias = int(sys.argv[1]) if len(sys.argv) > 1 else 30
    quick = False
    if len(sys.argv) > 2 and str(sys.argv[2]).lower() in ('q','quick','fast'):
        quick = True
    auditar_skus_sem_custo(dias, quick=quick)
