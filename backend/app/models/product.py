from sqlalchemy import Column, String, Integer, Numeric, Boolean, ForeignKey

from app.db.base import Base, MultiTenantMixin


class Product(MultiTenantMixin, Base):
    __tablename__ = "product"

    store_id = Column(Integer, ForeignKey("store.id", ondelete="SET NULL"), nullable=True)
    sku = Column(String(100), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    canal = Column(String(50), nullable=True)  # Canal de venda: Shopee, Mercado Livre, etc
    custo_atual = Column(Numeric(12, 2), nullable=True)  # Sincronizado do Tiny ERP - fonte de verdade para custo
    preco_venda = Column(Numeric(12, 2), nullable=True)  # Preço de venda no canal
    ativo = Column(Boolean, default=True, nullable=False)
