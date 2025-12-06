from sqlalchemy import Column, String, Boolean

from app.db.base import Base, MultiTenantMixin


class BoletoRule(MultiTenantMixin, Base):
    __tablename__ = "boletorule"

    cnpj = Column(String(20), nullable=False)
    fornecedor_sugerido = Column(String(255), nullable=True)
    categoria_sugerida = Column(String(100), nullable=True)
    ativo = Column(Boolean, default=True, nullable=False)
