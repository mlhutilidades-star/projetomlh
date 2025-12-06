from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps.deps import get_current_user, get_db
from app.models.store import Store
from app.models.user import User
from app.schemas.store import StoreCreate, StoreUpdate, StoreOut

router = APIRouter()


@router.get("", response_model=list[StoreOut])
def list_stores(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    stores = db.query(Store).filter(Store.tenant_id == current_user.tenant_id).all()
    return stores


@router.post("", response_model=StoreOut)
def create_store(payload: StoreCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    store = Store(tenant_id=current_user.tenant_id, **payload.dict())
    db.add(store)
    db.commit()
    db.refresh(store)
    return store


@router.patch("/{store_id}", response_model=StoreOut)
def update_store(store_id: int, payload: StoreUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    store = db.get(Store, store_id)
    if not store or store.tenant_id != current_user.tenant_id:
        raise HTTPException(status_code=404, detail="Store not found")
    for field, value in payload.dict(exclude_unset=True).items():
        setattr(store, field, value)
    db.add(store)
    db.commit()
    db.refresh(store)
    return store
