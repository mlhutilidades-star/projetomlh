from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, extract, case
from datetime import datetime, timedelta
from typing import Optional

from app.api.deps.deps import get_current_user, get_db
from app.models.user import User
from app.models.order import Order
from app.models.payout import Payout
from app.models.payable import Payable
from app.models.receivable import Receivable
from app.models.product import Product
from app.schemas.analytics import (
    ResumoFinanceiro,
    DREMensalResponse,
    DREMes,
    MargemProdutoLista,
    MargemProdutoItem,
    MargemCanalLista,
    MargemCanalItem,
    CurvaABCLista,
    CurvaABCItem,
    PrecificacaoLista,
    PrecificacaoItem,
    MargemLista,
    MargemItem,
)

router = APIRouter()


@router.get("/resumo-financeiro", response_model=ResumoFinanceiro)
def resumo_financeiro(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    tenant_id = current_user.tenant_id
    data_limite = datetime.utcnow() - timedelta(days=30)
    
    # Faturamento e lucro últimos 30 dias
    faturamento = db.query(func.coalesce(func.sum(Order.total_bruto), 0)).filter(
        Order.tenant_id == tenant_id,
        Order.data_pedido >= data_limite
    ).scalar() or 0
    taxas = db.query(func.coalesce(func.sum(Order.taxas), 0)).filter(
        Order.tenant_id == tenant_id,
        Order.data_pedido >= data_limite
    ).scalar() or 0
    fretes = db.query(func.coalesce(func.sum(Order.frete), 0)).filter(
        Order.tenant_id == tenant_id,
        Order.data_pedido >= data_limite
    ).scalar() or 0
    lucro_estimado = faturamento - taxas - fretes
    
    # Contas a pagar em aberto
    contas_pagar = db.query(func.coalesce(func.sum(Payable.valor_previsto), 0)).filter(
        Payable.tenant_id == tenant_id,
        Payable.status == "pendente"
    ).scalar() or 0
    
    # Contas a receber em aberto
    contas_receber = db.query(func.coalesce(func.sum(Receivable.valor_previsto), 0)).filter(
        Receivable.tenant_id == tenant_id,
        Receivable.status == "pendente"
    ).scalar() or 0
    
    # Saldo de repasses últimos 30 dias
    saldo_repasses = db.query(func.coalesce(func.sum(Payout.liquido), 0)).filter(
        Payout.tenant_id == tenant_id,
        Payout.created_at >= data_limite
    ).scalar() or 0
    
    # Ticket médio últimos 30 dias
    qtd_pedidos = db.query(func.count(Order.id)).filter(
        Order.tenant_id == tenant_id,
        Order.data_pedido >= data_limite
    ).scalar() or 0
    ticket_medio = float(faturamento / qtd_pedidos) if qtd_pedidos > 0 else 0.0

    return ResumoFinanceiro(
        faturamento_30d=float(faturamento),
        lucro_estimado_30d=float(lucro_estimado),
        contas_pagar_abertas=float(contas_pagar),
        contas_receber_abertas=float(contas_receber),
        saldo_repasses_30d=float(saldo_repasses),
        ticket_medio_30d=ticket_medio,
    )


@router.get("/dre-mensal", response_model=DREMensalResponse)
def dre_mensal(ano: int = Query(None), db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    tenant_id = current_user.tenant_id
    
    # Se ano não fornecido, usar ano atual
    if ano is None:
        from datetime import datetime
        ano = datetime.now().year
    
    meses_data = []
    
    for mes in range(1, 13):
        # Receitas brutas do mês
        receitas = db.query(func.coalesce(func.sum(Order.total_bruto), 0)).filter(
            Order.tenant_id == tenant_id,
            extract('year', Order.data_pedido) == ano,
            extract('month', Order.data_pedido) == mes
        ).scalar() or 0
        
        # Descontos/taxas
        taxas = db.query(func.coalesce(func.sum(Order.taxas), 0)).filter(
            Order.tenant_id == tenant_id,
            extract('year', Order.data_pedido) == ano,
            extract('month', Order.data_pedido) == mes
        ).scalar() or 0
        fretes = db.query(func.coalesce(func.sum(Order.frete), 0)).filter(
            Order.tenant_id == tenant_id,
            extract('year', Order.data_pedido) == ano,
            extract('month', Order.data_pedido) == mes
        ).scalar() or 0
        descontos_taxas = float(taxas) + float(fretes)
        
        # Custos de produto (estimativa: baseado em produtos vendidos)
        # Para simplicidade, assumimos 50% da receita líquida como custo
        receita_liquida = float(receitas) - descontos_taxas
        custos_produto = receita_liquida * 0.5
        
        # Despesas (payables pagos no mês)
        despesas = db.query(func.coalesce(func.sum(Payable.valor_previsto), 0)).filter(
            Payable.tenant_id == tenant_id,
            Payable.status == "pago",
            extract('year', Payable.vencimento) == ano,
            extract('month', Payable.vencimento) == mes
        ).scalar() or 0
        
        resultado = float(receitas) - descontos_taxas - custos_produto - float(despesas)
        
        meses_data.append(DREMes(
            mes=mes,
            ano=ano,
            receitas_brutas=float(receitas),
            descontos_taxas=float(descontos_taxas),
            custos_produto=float(custos_produto),
            despesas=float(despesas),
            resultado_liquido=float(resultado),
        ))
    
    return DREMensalResponse(ano=ano, meses=meses_data)


@router.get("/margem-por-produto", response_model=MargemProdutoLista)
def margem_por_produto(
    data_ini: Optional[str] = Query(None),
    data_fim: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Análise de margem por produto.
    
    Custo utilizado: custo_atual (sincronizado do Tiny ERP)
    Receita: soma de total_bruto dos pedidos
    """
    tenant_id = current_user.tenant_id
    
    # Parse dates
    if data_ini:
        dt_ini = datetime.fromisoformat(data_ini)
    else:
        dt_ini = datetime.utcnow() - timedelta(days=30)
    
    if data_fim:
        dt_fim = datetime.fromisoformat(data_fim)
    else:
        dt_fim = datetime.utcnow()
    
    produtos = db.query(Product).filter(Product.tenant_id == tenant_id).all()
    items = []
    
    for p in produtos:
        # Buscar vendas do produto no período (simulado: assumimos que Order não tem product_id, então fazemos estimativa geral)
        # Em produção real, seria necessário OrderItem para rastrear produtos individuais
        vendas_qtd = 1  # Placeholder
        receita = float(p.preco_venda or 0) * vendas_qtd
        custo = float(p.custo_atual or 0) * vendas_qtd
        margem_val = receita - custo
        margem_pct = (margem_val / receita * 100) if receita > 0 else 0.0
        
        items.append(MargemProdutoItem(
            sku=p.sku,
            nome=p.name,
            vendas_qtd=vendas_qtd,
            receita_liquida=receita,
            custo_total=custo,
            margem_valor=margem_val,
            margem_percentual=margem_pct,
        ))
    
    return MargemProdutoLista(itens=items)


@router.get("/margem-por-canal", response_model=MargemCanalLista)
def margem_por_canal_novo(
    data_ini: Optional[str] = Query(None),
    data_fim: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    tenant_id = current_user.tenant_id
    
    if data_ini:
        dt_ini = datetime.fromisoformat(data_ini)
    else:
        dt_ini = datetime.utcnow() - timedelta(days=30)
    
    if data_fim:
        dt_fim = datetime.fromisoformat(data_fim)
    else:
        dt_fim = datetime.utcnow()
    
    rows = db.query(
        Order.canal,
        func.coalesce(func.sum(Order.total_bruto), 0).label('receita'),
        func.coalesce(func.sum(Order.taxas), 0).label('taxas'),
        func.coalesce(func.sum(Order.frete), 0).label('frete')
    ).filter(
        Order.tenant_id == tenant_id,
        Order.data_pedido >= dt_ini,
        Order.data_pedido <= dt_fim
    ).group_by(Order.canal).all()
    
    items = []
    for row in rows:
        receita = float(row.receita)
        taxas = float(row.taxas) + float(row.frete)
        custo = receita * 0.5  # Estimativa: 50% de custo
        receita_liq = receita - taxas
        margem_val = receita_liq - custo
        margem_pct = (margem_val / receita_liq * 100) if receita_liq > 0 else 0.0
        
        items.append(MargemCanalItem(
            canal=row.canal or "N/A",
            receita_liquida=receita_liq,
            custo_total=custo,
            margem_valor=margem_val,
            margem_percentual=margem_pct,
        ))
    
    return MargemCanalLista(itens=items)


@router.get("/curva-abc", response_model=CurvaABCLista)
def curva_abc(
    data_ini: Optional[str] = Query(None),
    data_fim: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Curva ABC de produtos por faturamento (regra de Pareto).
    
    Classificação:
    - Classe A: 0-80% (produtos que geram 80% da receita)
    - Classe B: 80-95% (próximos produtos)
    - Classe C: 95-100% (restantes - baixo impacto)
    
    Custo: custo_atual sincronizado do Tiny ERP
    """
    tenant_id = current_user.tenant_id
    
    if data_ini:
        dt_ini = datetime.fromisoformat(data_ini)
    else:
        dt_ini = datetime.utcnow() - timedelta(days=90)
    
    if data_fim:
        dt_fim = datetime.fromisoformat(data_fim)
    else:
        dt_fim = datetime.utcnow()
    
    # Buscar produtos e calcular receita (simulado)
    produtos = db.query(Product).filter(Product.tenant_id == tenant_id).all()
    produtos_receita = []
    for p in produtos:
        receita = float(p.preco_venda or 0)  # Placeholder: em produção seria sum(OrderItem.total)
        produtos_receita.append((p.sku, p.name, receita))
    
    # Ordenar por receita decrescente
    produtos_receita.sort(key=lambda x: x[2], reverse=True)
    
    # Calcular total e acumulado
    total_receita = sum(x[2] for x in produtos_receita)
    items = []
    acumulado = 0.0
    
    for sku, nome, receita in produtos_receita:
        acumulado += receita
        pct_acum = (acumulado / total_receita * 100) if total_receita > 0 else 0.0
        
        # Classificar ABC
        if pct_acum <= 80:
            classe = "A"
        elif pct_acum <= 95:
            classe = "B"
        else:
            classe = "C"
        
        items.append(CurvaABCItem(
            sku=sku,
            nome=nome,
            receita=receita,
            percentual_acumulado=pct_acum,
            classe=classe,
        ))
    
    return CurvaABCLista(itens=items)


@router.get("/precificacao-sugerida", response_model=PrecificacaoLista)
def precificacao_sugerida(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """
    Sugestão de preços com margens desejadas.
    
    Custo base: custo_atual do Tiny ERP
    Fórmula: preço = custo / (1 - taxa_média - margem_desejada)
    Taxa média: 15% (estimativa de taxas plataforma + processamento)
    
    Margens sugeridas:
    - 20%: margem conservadora
    - 30%: margem agressiva
    """
    tenant_id = current_user.tenant_id
    produtos = db.query(Product).filter(Product.tenant_id == tenant_id).all()
    items = []
    
    for p in produtos:
        custo = float(p.custo_atual or 0)
        preco = float(p.preco_venda or 0)
        
        # Taxa média estimada (15% para simplicidade)
        taxa_media = 0.15
        
        # Preço sugerido para 20% de margem
        # Fórmula: preco = custo / (1 - taxa - margem_desejada)
        preco_sug_20 = custo / (1 - taxa_media - 0.20) if (1 - taxa_media - 0.20) > 0 else 0.0
        preco_sug_30 = custo / (1 - taxa_media - 0.30) if (1 - taxa_media - 0.30) > 0 else 0.0
        
        items.append(PrecificacaoItem(
            sku=p.sku,
            nome=p.name,
            custo_atual=custo,
            preco_atual=preco,
            preco_sugerido_20=preco_sug_20,
            preco_sugerido_30=preco_sug_30,
        ))
    
    return PrecificacaoLista(itens=items)


# Legacy endpoints (manter compatibilidade)
@router.get("/margem-por-produto-legacy", response_model=MargemLista)
def margem_por_produto_legacy(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    tenant_id = current_user.tenant_id
    produtos = db.query(Product).filter(Product.tenant_id == tenant_id).all()
    items = []
    for p in produtos:
        margem = float((p.preco_venda or 0) - (p.custo_atual or 0))
        items.append(MargemItem(chave=p.name, margem=margem))
    return MargemLista(itens=items)


@router.get("/margem-por-canal-legacy", response_model=MargemLista)
def margem_por_canal_legacy(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    tenant_id = current_user.tenant_id
    rows = db.query(Order.canal, func.coalesce(func.sum(Order.liquido), 0)).filter(Order.tenant_id == tenant_id).group_by(Order.canal).all()
    items = [MargemItem(chave=row[0] or "N/A", margem=float(row[1])) for row in rows]
    return MargemLista(itens=items)
