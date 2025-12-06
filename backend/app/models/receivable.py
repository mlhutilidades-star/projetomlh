from sqlalchemy import Column, String, Numeric, Date, Integer

from app.db.base import Base, MultiTenantMixin


class Receivable(MultiTenantMixin, Base):
    __tablename__ = "receivable"

    origem = Column(String(50), nullable=True)
    referencia = Column(String(255), nullable=False)
    previsao = Column(Date, nullable=True)
    valor_previsto = Column(Numeric(12, 2), nullable=False)
    status = Column(String(50), nullable=False, default="pendente")
