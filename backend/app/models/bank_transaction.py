from sqlalchemy import Column, String, Numeric, Date, Boolean

from app.db.base import Base, MultiTenantMixin


class BankTransaction(MultiTenantMixin, Base):
    __tablename__ = "banktransaction"

    banco = Column(String(100), nullable=False)
    data = Column(Date, nullable=False)
    valor = Column(Numeric(12, 2), nullable=False)
    tipo = Column(String(10), nullable=False)  # credito/debito
    descricao = Column(String(255), nullable=True)
    conciliado = Column(Boolean, default=False, nullable=False)
