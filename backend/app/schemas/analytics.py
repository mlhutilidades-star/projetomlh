from typing import List
from pydantic import BaseModel


class ResumoFinanceiro(BaseModel):
    faturamento_30d: float
    lucro_estimado_30d: float
    contas_pagar_abertas: float
    contas_receber_abertas: float
    saldo_repasses_30d: float
    ticket_medio_30d: float


class DREMes(BaseModel):
    mes: int
    ano: int
    receitas_brutas: float
    descontos_taxas: float
    custos_produto: float
    despesas: float
    resultado_liquido: float


class DREMensalResponse(BaseModel):
    ano: int
    meses: List[DREMes]


class MargemProdutoItem(BaseModel):
    sku: str
    nome: str
    vendas_qtd: int
    receita_liquida: float
    custo_total: float
    margem_valor: float
    margem_percentual: float


class MargemProdutoLista(BaseModel):
    itens: List[MargemProdutoItem]


class MargemCanalItem(BaseModel):
    canal: str
    receita_liquida: float
    custo_total: float
    margem_valor: float
    margem_percentual: float


class MargemCanalLista(BaseModel):
    itens: List[MargemCanalItem]


class CurvaABCItem(BaseModel):
    sku: str
    nome: str
    receita: float
    percentual_acumulado: float
    classe: str


class CurvaABCLista(BaseModel):
    itens: List[CurvaABCItem]


class PrecificacaoItem(BaseModel):
    sku: str
    nome: str
    custo_atual: float
    preco_atual: float
    preco_sugerido_20: float
    preco_sugerido_30: float


class PrecificacaoLista(BaseModel):
    itens: List[PrecificacaoItem]


# Legacy schemas (manter compatibilidade)
class MargemItem(BaseModel):
    chave: str
    margem: float


class MargemLista(BaseModel):
    itens: List[MargemItem]
