"""
Analytics helpers for Hub Financeiro

Provide aggregate KPIs, categorical breakdowns, and monthly series,
including revenue vs expense segregation. Revenue is identified by
categoria starting with 'Receita'. Everything else is treated as expense.
"""

from __future__ import annotations
from typing import Dict, List, Tuple, Optional
from sqlalchemy import func
from datetime import date, datetime, timedelta

from .database import get_db, ContaPagar
from .cache import cached


def _is_revenue(categoria: str | None) -> bool:
    if not categoria:
        return False
    return categoria.strip().lower().startswith('receita')


@cached(ttl_seconds=300)
def kpis_global(db=None, data_inicio: Optional[date] = None, data_fim: Optional[date] = None) -> Dict:
    """Compute key KPIs: total contas, pendentes, vencidas, valor pendente,
    receita total (últimos 90 dias), despesa total (últimos 90 dias), saldo líquido.
    
    Args:
        db: Sessão de banco de dados (opcional)
        data_inicio: Data inicial do período (padrão: hoje - 90 dias)
        data_fim: Data final do período (padrão: hoje)
    """
    should_close = False
    if db is None:
        db = get_db()
        should_close = True
    try:
        hoje = data_fim or date.today()
        d90 = data_inicio or (hoje - timedelta(days=90))

        # Base query para período
        base_query = db.query(ContaPagar).filter(ContaPagar.vencimento.between(d90, hoje))

        total_contas = db.query(func.count(ContaPagar.id)).scalar() or 0
        pendentes = db.query(func.count(ContaPagar.id)).filter(ContaPagar.status == 'Pendente').scalar() or 0
        valor_pendente = db.query(func.sum(ContaPagar.valor)).filter(ContaPagar.status == 'Pendente').scalar() or 0.0
        vencidas = db.query(func.count(ContaPagar.id)).filter(ContaPagar.vencimento < hoje, ContaPagar.status == 'Pendente').scalar() or 0

        # Receita e despesa no período especificado
        receitas_periodo = db.query(func.sum(ContaPagar.valor)).filter(
            ContaPagar.vencimento.between(d90, hoje),
            ContaPagar.categoria.isnot(None)
        ).filter(ContaPagar.categoria.like('Receita%')).scalar() or 0.0

        # COGS (Custo do Produto) - usado para margem de contribuição
        cogs_periodo = db.query(func.sum(ContaPagar.valor)).filter(
            ContaPagar.vencimento.between(d90, hoje),
            ContaPagar.categoria == 'Despesa Venda - Custo Produto (Tiny)'
        ).scalar() or 0.0

        # Outras despesas (exclui receitas e COGS) para visão de custos operacionais
        despesas_periodo = db.query(func.sum(ContaPagar.valor)).filter(
            ContaPagar.vencimento.between(d90, hoje)
        ).filter(~ContaPagar.categoria.like('Receita%')).filter(
            ContaPagar.categoria != 'Despesa Venda - Custo Produto (Tiny)'
        ).scalar() or 0.0

        # Saldo líquido tradicional (Receita - Todas as despesas incluindo COGS)
        saldo_periodo = float(receitas_periodo) - float(despesas_periodo) - float(cogs_periodo)

        # Margem de contribuição (Receita - Custo do Produto)
        margem_contrib_valor = float(receitas_periodo) - float(cogs_periodo)
        margem_contrib_percent = (margem_contrib_valor / receitas_periodo * 100.0) if receitas_periodo > 0 else 0.0

        return {
            'total_contas': int(total_contas),
            'pendentes': int(pendentes),
            'valor_pendente': float(valor_pendente or 0.0),
            'vencidas': int(vencidas),
            'receitas_periodo': float(receitas_periodo),
            'cogs_periodo': float(cogs_periodo),
            'despesas_periodo': float(despesas_periodo),
            'saldo_periodo': float(saldo_periodo),
            'margem_contrib_valor': float(margem_contrib_valor),
            'margem_contrib_percent': float(margem_contrib_percent),
            'data_inicio': d90,
            'data_fim': hoje
        }
    finally:
        if should_close:
            db.close()


@cached(ttl_seconds=300)
def categorias_sum(db=None, data_inicio: Optional[date] = None, data_fim: Optional[date] = None) -> List[Tuple[str, float]]:
    """Return list of (categoria, soma_valor) sorted desc.
    
    Args:
        db: Sessão de banco de dados (opcional)
        data_inicio: Data inicial do período (opcional)
        data_fim: Data final do período (opcional)
    """
    should_close = False
    if db is None:
        db = get_db()
        should_close = True
    try:
        query = db.query(ContaPagar.categoria, func.sum(ContaPagar.valor).label('valor')).\
            filter(ContaPagar.categoria.isnot(None))
        
        if data_inicio:
            query = query.filter(ContaPagar.vencimento >= data_inicio)
        if data_fim:
            query = query.filter(ContaPagar.vencimento <= data_fim)
        
        rows = query.group_by(ContaPagar.categoria).\
            order_by(func.sum(ContaPagar.valor).desc()).\
            all()
        return [(r[0], float(r[1] or 0.0)) for r in rows]
    finally:
        if should_close:
            db.close()


@cached(ttl_seconds=300)
def top_fornecedores(db=None, limit: int = 5, data_inicio: Optional[date] = None, data_fim: Optional[date] = None) -> List[Tuple[str, float]]:
    """Top fornecedores por soma de valor.
    
    Args:
        db: Sessão de banco de dados (opcional)
        limit: Número máximo de fornecedores (padrão: 5)
        data_inicio: Data inicial do período (opcional)
        data_fim: Data final do período (opcional)
    """
    should_close = False
    if db is None:
        db = get_db()
        should_close = True
    try:
        query = db.query(ContaPagar.fornecedor, func.sum(ContaPagar.valor).label('valor'))
        
        if data_inicio:
            query = query.filter(ContaPagar.vencimento >= data_inicio)
        if data_fim:
            query = query.filter(ContaPagar.vencimento <= data_fim)
        
        rows = query.group_by(ContaPagar.fornecedor).\
            order_by(func.sum(ContaPagar.valor).desc()).\
            limit(limit).\
            all()
        return [(r[0], float(r[1] or 0.0)) for r in rows]
    finally:
        if should_close:
            db.close()


@cached(ttl_seconds=300)
def monthly_series(db=None, ano: Optional[int] = None) -> Dict:
    """Return monthly aggregated series for receita and despesa.
    Output: {
      'mes': [1..12], 'receita': [..], 'despesa': [..], 'total': [..]
    }
    
    Args:
        db: Sessão de banco de dados (opcional)
        ano: Ano específico para filtrar (padrão: ano atual)
    """
    should_close = False
    if db is None:
        db = get_db()
        should_close = True
    try:
        query = db.query(ContaPagar.mes, ContaPagar.categoria, func.sum(ContaPagar.valor).label('valor'))
        
        if ano:
            data_inicio = date(ano, 1, 1)
            data_fim = date(ano, 12, 31)
            query = query.filter(ContaPagar.vencimento.between(data_inicio, data_fim))
        
        rows = query.group_by(ContaPagar.mes, ContaPagar.categoria).\
            order_by(ContaPagar.mes).\
            all()
        receita = {i: 0.0 for i in range(1, 13)}
        despesa = {i: 0.0 for i in range(1, 13)}
        for m, cat, v in rows:
            if _is_revenue(cat):
                receita[m] = receita.get(m, 0.0) + float(v or 0.0)
            else:
                despesa[m] = despesa.get(m, 0.0) + float(v or 0.0)
        total = {m: receita.get(m, 0.0) + despesa.get(m, 0.0) for m in range(1, 13)}
        return {
            'mes': list(range(1, 13)),
            'receita': [receita[m] for m in range(1, 13)],
            'despesa': [despesa[m] for m in range(1, 13)],
            'total': [total[m] for m in range(1, 13)]
        }
    finally:
        if should_close:
            db.close()


def shopee_stats(db=None, days: int = 90) -> Dict:
    """Return Shopee-specific stats within the last N days."""
    should_close = False
    if db is None:
        db = get_db()
        should_close = True
    try:
        today = date.today()
        since = today - timedelta(days=days)
        count = db.query(func.count(ContaPagar.id)).\
            filter(ContaPagar.descricao.like('%Pedido Shopee%'), ContaPagar.vencimento >= since).\
            scalar() or 0
        total = db.query(func.sum(ContaPagar.valor)).\
            filter(ContaPagar.descricao.like('%Pedido Shopee%'), ContaPagar.vencimento >= since).\
            scalar() or 0.0
        return {'count': int(count), 'total': float(total or 0.0)}
    finally:
        if should_close:
            db.close()

def cogs_fill_rate(db=None, data_inicio: Optional[date] = None, data_fim: Optional[date] = None) -> Dict:
    """Avalia a taxa de preenchimento de Custo do Produto (COGS) para pedidos Shopee.

    Considera pedidos com categoria de receita ("Receita%") e verifica quantos
    possuem entrada correspondente de COGS (categoria == 'Despesa Venda - Custo Produto (Tiny)')
    dentro do período. A correspondência é feita por extração do order_sn em observacoes (padrão 'SN:XXXX').
    """
    should_close = False
    if db is None:
        db = get_db()
        should_close = True
    try:
        hoje = date.today()
        inicio = data_inicio or (hoje - timedelta(days=90))
        fim = data_fim or hoje

        receitas = db.query(ContaPagar.observacoes).filter(
            ContaPagar.vencimento.between(inicio, fim),
            ContaPagar.categoria.like('Receita%'),
            ContaPagar.observacoes.isnot(None)
        ).all()

        cogs = db.query(ContaPagar.observacoes).filter(
            ContaPagar.vencimento.between(inicio, fim),
            ContaPagar.categoria == 'Despesa Venda - Custo Produto (Tiny)',
            ContaPagar.observacoes.isnot(None)
        ).all()

        def extract_order_sn(obs: str) -> str | None:
            if not obs:
                return None
            # Observações contêm 'SN:xxxxx'
            for part in obs.split('|'):
                part = part.strip()
                if part.startswith('SN:'):
                    return part.replace('SN:','').strip()
            return None

        receita_sns = {extract_order_sn(r[0]) for r in receitas if extract_order_sn(r[0])}
        cogs_sns = {extract_order_sn(c[0]) for c in cogs if extract_order_sn(c[0])}

        pedidos_receita = len(receita_sns)
        pedidos_cogs = len(receita_sns.intersection(cogs_sns))
        fill_rate = (pedidos_cogs / pedidos_receita * 100.0) if pedidos_receita > 0 else 0.0

        return {
            'pedidos_receita': pedidos_receita,
            'pedidos_cogs': pedidos_cogs,
            'fill_rate_percent': fill_rate,
            'inicio': inicio,
            'fim': fim
        }
    finally:
        if should_close:
            db.close()
