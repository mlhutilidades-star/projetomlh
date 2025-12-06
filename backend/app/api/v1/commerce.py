from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps.deps import get_current_user, get_db
from app.models.user import User
from app.models.product import Product
from app.models.order import Order
from app.models.payout import Payout
from app.schemas.commerce import ProductOut, OrderOut, PayoutOut

router = APIRouter(prefix="")


@router.get("/products", response_model=list[ProductOut])
def list_products(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return db.query(Product).filter(Product.tenant_id == current_user.tenant_id).all()


@router.get("/orders", response_model=list[OrderOut])
def list_orders(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return db.query(Order).filter(Order.tenant_id == current_user.tenant_id).all()


@router.get("/payouts", response_model=list[PayoutOut])
def list_payouts(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return db.query(Payout).filter(Payout.tenant_id == current_user.tenant_id).all()
