from fastapi import APIRouter

from app.api.v1 import auth, tenants, stores, finance, commerce, analytics, sync

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(tenants.router, prefix="/tenants", tags=["tenants"])
api_router.include_router(stores.router, prefix="/stores", tags=["stores"])
api_router.include_router(finance.router, prefix="/finance", tags=["finance"])
api_router.include_router(commerce.router, tags=["commerce"])
api_router.include_router(sync.router, prefix="/sync", tags=["sync"])
api_router.include_router(analytics.router, prefix="/analytics", tags=["analytics"])
