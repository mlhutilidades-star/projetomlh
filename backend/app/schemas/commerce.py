from datetime import datetime, date
from typing import Optional
from pydantic import BaseModel


class ProductOut(BaseModel):
    id: int
    tenant_id: int
    store_id: Optional[int]
    sku: str
    name: str
    canal: Optional[str]
    custo_atual: Optional[float]
    preco_venda: Optional[float]
    ativo: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class OrderOut(BaseModel):
    id: int
    tenant_id: int
    store_id: Optional[int]
    codigo_externo: str
    canal: Optional[str]
    status: Optional[str]
    total_bruto: Optional[float]
    taxas: Optional[float]
    frete: Optional[float]
    liquido: Optional[float]
    data_pedido: Optional[datetime]

    class Config:
        from_attributes = True


class PayoutOut(BaseModel):
    id: int
    tenant_id: int
    store_id: Optional[int]
    referencia_periodo: str
    valor_bruto: Optional[float]
    taxas: Optional[float]
    frete: Optional[float]
    liquido: Optional[float]
    data_repassado: Optional[date]

    class Config:
        from_attributes = True
