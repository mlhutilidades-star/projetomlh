from typing import Optional
from pydantic import BaseModel


class StoreBase(BaseModel):
    name: str
    tipo_canal: str
    credenciais: Optional[dict] = None
    ativo: bool = True


class StoreCreate(StoreBase):
    pass


class StoreUpdate(BaseModel):
    name: Optional[str] = None
    tipo_canal: Optional[str] = None
    credenciais: Optional[dict] = None
    ativo: Optional[bool] = None


class StoreOut(StoreBase):
    id: int
    tenant_id: int

    class Config:
        from_attributes = True
