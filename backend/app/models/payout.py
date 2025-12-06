from sqlalchemy import Column, String, Integer, Numeric, Date, ForeignKey

from app.db.base import Base, MultiTenantMixin


class Payout(MultiTenantMixin, Base):
    __tablename__ = "payout"

    store_id = Column(Integer, ForeignKey("store.id", ondelete="SET NULL"), nullable=True)
    referencia_periodo = Column(String(100), nullable=False)
    valor_bruto = Column(Numeric(12, 2), nullable=True)
    taxas = Column(Numeric(12, 2), nullable=True)
    frete = Column(Numeric(12, 2), nullable=True)
    liquido = Column(Numeric(12, 2), nullable=True)
    data_repassado = Column(Date, nullable=True)
