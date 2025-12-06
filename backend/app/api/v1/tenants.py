from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps.deps import get_current_user, get_db
from app.models.tenant import Tenant
from app.models.user import User

router = APIRouter()


@router.get("/me")
def get_tenant_me(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    tenant = db.get(Tenant, current_user.tenant_id)
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    return tenant
