from datetime import date, datetime
from typing import Optional
from pydantic import BaseModel

from app.models.boleto_upload import BoletoStatus


class PayableBase(BaseModel):
    fornecedor: str
    categoria: Optional[str] = None
    vencimento: date
    valor_previsto: float
    status: str = "pendente"
    origem: Optional[str] = None
    boleto_upload_id: Optional[int] = None


class PayableCreate(PayableBase):
    pass


class PayableOut(PayableBase):
    id: int
    tenant_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ReceivableBase(BaseModel):
    origem: Optional[str] = None
    referencia: str
    previsao: Optional[date] = None
    valor_previsto: float
    status: str = "pendente"


class ReceivableCreate(ReceivableBase):
    pass


class ReceivableOut(ReceivableBase):
    id: int
    tenant_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class BoletoUploadOut(BaseModel):
    id: int
    tenant_id: int
    status: BoletoStatus
    mensagem_erro: Optional[str] = None

    class Config:
        from_attributes = True
