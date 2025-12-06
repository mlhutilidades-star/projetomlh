from sqlalchemy import Column, String, Numeric, Date, Enum
import enum

from app.db.base import Base, MultiTenantMixin


class BoletoStatus(str, enum.Enum):
    pendente = "pendente"
    processado = "processado"
    erro = "erro"


class BoletoUpload(MultiTenantMixin, Base):
    __tablename__ = "boletoupload"

    arquivo_path = Column(String(255), nullable=True)
    cnpj = Column(String(20), nullable=True)
    vencimento = Column(Date, nullable=True)
    valor = Column(Numeric(12, 2), nullable=True)
    linha_digitavel = Column(String(255), nullable=True)
    status = Column(Enum(BoletoStatus), default=BoletoStatus.pendente, nullable=False)
    mensagem_erro = Column(String(255), nullable=True)
