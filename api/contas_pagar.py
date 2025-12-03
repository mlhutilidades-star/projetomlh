from fastapi import FastAPI, HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models.contas_pagar import Base, ContaPagar, StatusConta
from pydantic import BaseModel
from typing import List, Optional
from datetime import date

DATABASE_URL = "sqlite:///./mlh.db"

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

    class Config:
        orm_mode = True

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
