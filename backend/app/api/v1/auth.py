from fastapi import APIRouter, Depends, HTTPException, status, Body
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordRequestForm

from app.api.deps.deps import get_db, get_current_user
from app.core.config import get_settings
from app.core.security import get_password_hash, verify_password, create_token, decode_token
from app.models.user import User
from app.models.tenant import Tenant
from app.schemas.auth import RegisterTenantRequest, LoginRequest, Token, UserOut

router = APIRouter()
settings = get_settings()


@router.post("/register-tenant", response_model=UserOut)
def register_tenant(payload: RegisterTenantRequest, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == payload.admin_email).first()
    if existing:
        raise HTTPException(status_code=400, detail="User with this email already exists")

    tenant = Tenant(name=payload.tenant_name, plan=payload.tenant_plan, tenant_id=0)
    db.add(tenant)
    db.flush()
    tenant.tenant_id = tenant.id

    user = User(
        tenant_id=tenant.id,
        name=payload.admin_name,
        email=payload.admin_email,
        password_hash=get_password_hash(payload.admin_password),
        role="admin",
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.post("/login", response_model=Token)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email).first()
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    # JWT "sub" must be a string per spec; using str(user.id) to avoid jose JWTClaimsError
    access_token = create_token({"sub": str(user.id), "tenant_id": user.tenant_id}, settings.jwt_secret_key, settings.access_token_expire_minutes)
    refresh_token = create_token({"sub": str(user.id), "tenant_id": user.tenant_id}, settings.jwt_refresh_secret_key, settings.refresh_token_expire_minutes)
    return Token(access_token=access_token, refresh_token=refresh_token)


@router.post("/refresh", response_model=Token)
def refresh_token(refresh_token: str = Body(..., embed=True), db: Session = Depends(get_db)):
    payload = decode_token(refresh_token, settings.jwt_refresh_secret_key)
    if payload is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")
    user_id = payload.get("sub")
    tenant_id = payload.get("tenant_id")
    user = db.get(User, user_id)
    if not user or user.tenant_id != tenant_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token user")
    # Ensure string subject to satisfy JWT spec
    access_token = create_token({"sub": str(user.id), "tenant_id": user.tenant_id}, settings.jwt_secret_key, settings.access_token_expire_minutes)
    new_refresh = create_token({"sub": str(user.id), "tenant_id": user.tenant_id}, settings.jwt_refresh_secret_key, settings.refresh_token_expire_minutes)
    return Token(access_token=access_token, refresh_token=new_refresh)


@router.get("/me", response_model=UserOut)
def me(current_user: User = Depends(get_current_user)):
    return current_user
