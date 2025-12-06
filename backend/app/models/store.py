from sqlalchemy import Column, String, Integer, Boolean, JSON
from app.db.base import Base, MultiTenantMixin


class Store(MultiTenantMixin, Base):
    __tablename__ = "store"

    name = Column(String(255), nullable=False)
    tipo_canal = Column(String(50), nullable=False)
    credenciais = Column(JSON, nullable=True)
    ativo = Column(Boolean, default=True, nullable=False)
