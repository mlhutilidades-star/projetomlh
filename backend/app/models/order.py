from sqlalchemy import Column, String, Integer, Numeric, DateTime, ForeignKey

from app.db.base import Base, MultiTenantMixin


class Order(MultiTenantMixin, Base):
    __tablename__ = "order"

    store_id = Column(Integer, ForeignKey("store.id", ondelete="SET NULL"), nullable=True)
    codigo_externo = Column(String(100), nullable=False, index=True)
    canal = Column(String(50), nullable=True)
    status = Column(String(50), nullable=True)
    total_bruto = Column(Numeric(12, 2), nullable=True)
    taxas = Column(Numeric(12, 2), nullable=True)
    frete = Column(Numeric(12, 2), nullable=True)
    liquido = Column(Numeric(12, 2), nullable=True)
    data_pedido = Column(DateTime(timezone=True), nullable=True)
