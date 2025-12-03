from fastapi import FastAPI, HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models.contas_pagar import Base, ContaPagar, StatusConta
from pydantic import BaseModel
from typing import List, Optional
from datetime import date
import os

# Usar DATABASE_URL do ambiente ou fallback para mlh.db
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./mlh.db")

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base.metadata.create_all(bind=engine)

app = FastAPI()

class ContaPagarCreate(BaseModel):
    descricao: str
    valor: float
    data_vencimento: date
    fornecedor: Optional[str] = None

class ContaPagarOut(BaseModel):
    id: int
    descricao: str
    valor: float
    data_vencimento: date
    status: StatusConta
    data_pagamento: Optional[date]
    fornecedor: Optional[str]

    model_config = {"from_attributes": True}

@app.get("/contas_pagar/", response_model=List[ContaPagarOut])
def listar_contas():
    db = SessionLocal()
    contas = db.query(ContaPagar).all()
    db.close()
    return contas

@app.post("/contas_pagar/", response_model=ContaPagarOut)
def criar_conta(conta: ContaPagarCreate):
    db = SessionLocal()
    nova_conta = ContaPagar(
        descricao=conta.descricao,
        valor=conta.valor,
        data_vencimento=conta.data_vencimento,
        status=StatusConta.pendente,
        fornecedor=conta.fornecedor
    )
    db.add(nova_conta)
    db.commit()
    db.refresh(nova_conta)
    db.close()
    return nova_conta

@app.patch("/contas_pagar/{conta_id}/pagar", response_model=ContaPagarOut)
def marcar_como_paga(conta_id: int, data_pagamento: Optional[date] = None):
    db = SessionLocal()
    conta = db.query(ContaPagar).filter(ContaPagar.id == conta_id).first()
    if not conta:
        db.close()
        raise HTTPException(status_code=404, detail="Conta não encontrada")
    conta.status = StatusConta.paga
    conta.data_pagamento = data_pagamento or date.today()
    db.commit()
    db.refresh(conta)
    db.close()
    return conta

@app.put("/contas_pagar/{conta_id}", response_model=ContaPagarOut)
def editar_conta(conta_id: int, conta_update: ContaPagarCreate):
    db = SessionLocal()
    conta = db.query(ContaPagar).filter(ContaPagar.id == conta_id).first()
    if not conta:
        db.close()
        raise HTTPException(status_code=404, detail="Conta não encontrada")
    conta.descricao = conta_update.descricao
    conta.valor = conta_update.valor
    conta.data_vencimento = conta_update.data_vencimento
    conta.fornecedor = conta_update.fornecedor
    db.commit()
    db.refresh(conta)
    db.close()
    return conta

@app.delete("/contas_pagar/{conta_id}", response_model=ContaPagarOut)
def excluir_conta(conta_id: int):
    db = SessionLocal()
    conta = db.query(ContaPagar).filter(ContaPagar.id == conta_id).first()
    if not conta:
        db.close()
        raise HTTPException(status_code=404, detail="Conta não encontrada")
    db.delete(conta)
    db.commit()
    db.close()
    return conta
