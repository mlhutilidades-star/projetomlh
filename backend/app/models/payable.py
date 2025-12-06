from sqlalchemy import Column, String, Integer, Numeric, Date, ForeignKey

from app.db.base import Base, MultiTenantMixin


class Payable(MultiTenantMixin, Base):
    __tablename__ = "payable"

    fornecedor = Column(String(255), nullable=False)
    categoria = Column(String(100), nullable=True)
    vencimento = Column(Date, nullable=False)
    valor_previsto = Column(Numeric(12, 2), nullable=False)
    status = Column(String(50), nullable=False, default="pendente")
    origem = Column(String(50), nullable=True)
    boleto_upload_id = Column(Integer, ForeignKey("boletoupload.id", ondelete="SET NULL"), nullable=True)
