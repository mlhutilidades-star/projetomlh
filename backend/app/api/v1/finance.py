from datetime import date
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session

from app.api.deps.deps import get_current_user, get_db
from app.models.user import User
from app.models.payable import Payable
from app.models.receivable import Receivable
from app.models.boleto_upload import BoletoUpload, BoletoStatus
from app.models.boleto_rule import BoletoRule
from app.schemas.finance import PayableCreate, PayableOut, ReceivableCreate, ReceivableOut, BoletoUploadOut

router = APIRouter()


@router.get("/payables", response_model=list[PayableOut])
def list_payables(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return db.query(Payable).filter(Payable.tenant_id == current_user.tenant_id).all()


@router.post("/payables", response_model=PayableOut)
def create_payable(payload: PayableCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    payable = Payable(tenant_id=current_user.tenant_id, **payload.dict())
    db.add(payable)
    db.commit()
    db.refresh(payable)
    return payable


@router.get("/receivables", response_model=list[ReceivableOut])
def list_receivables(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return db.query(Receivable).filter(Receivable.tenant_id == current_user.tenant_id).all()


@router.post("/receivables", response_model=ReceivableOut)
def create_receivable(payload: ReceivableCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    receivable = Receivable(tenant_id=current_user.tenant_id, **payload.dict())
    db.add(receivable)
    db.commit()
    db.refresh(receivable)
    return receivable


@router.post("/upload-boleto", response_model=BoletoUploadOut)
async def upload_boleto(file: UploadFile = File(...), db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    # Mock parse boleto
    suggested_cnpj = "00000000000000"
    rule = db.query(BoletoRule).filter(BoletoRule.tenant_id == current_user.tenant_id, BoletoRule.cnpj == suggested_cnpj, BoletoRule.ativo.is_(True)).first()

    boleto_upload = BoletoUpload(
        tenant_id=current_user.tenant_id,
        arquivo_path=file.filename,
        cnpj=suggested_cnpj,
        vencimento=date.today(),
        valor=100.00,
        linha_digitavel="mock",
        status=BoletoStatus.processado,
        mensagem_erro=None,
    )
    db.add(boleto_upload)
    db.flush()

    payable = Payable(
        tenant_id=current_user.tenant_id,
        fornecedor=rule.fornecedor_sugerido if rule else "Fornecedor Mock",
        categoria=rule.categoria_sugerida if rule else "Categoria",
        vencimento=boleto_upload.vencimento or date.today(),
        valor_previsto=boleto_upload.valor or 0,
        status="pendente",
        origem="boleto",
        boleto_upload_id=boleto_upload.id,
    )
    db.add(payable)
    db.commit()
    return boleto_upload
