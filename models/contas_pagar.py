from sqlalchemy import Column, Integer, String, Numeric, Date, Enum
from sqlalchemy.ext.declarative import declarative_base
import enum

Base = declarative_base()

class StatusConta(enum.Enum):
    pendente = "pendente"
    paga = "paga"

class ContaPagar(Base):
    __tablename__ = "contas_pagar"

    id = Column(Integer, primary_key=True, autoincrement=True)
    descricao = Column(String, nullable=False)
    valor = Column(Numeric(10, 2), nullable=False)
    data_vencimento = Column(Date, nullable=False)
    status = Column(Enum(StatusConta), default=StatusConta.pendente, nullable=False)
    data_pagamento = Column(Date, nullable=True)
    fornecedor = Column(String, nullable=True)
