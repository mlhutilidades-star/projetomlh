from fastapi import APIRouter, Depends
from redis import Redis
from rq import Queue
from fastapi import HTTPException, status

from app.api.deps.deps import get_current_user
from app.core.config import get_settings
from app.models.user import User
from app.tasks.jobs import sync_shopee_orders_task, sync_tiny_products_task, reconcile_bank_transactions_task
from app.services import ShopeeService, TinyService

router = APIRouter()
settings = get_settings()
redis_conn = Redis.from_url(settings.redis_url)
queue = Queue("default", connection=redis_conn)


@router.post("/shopee/orders")
def trigger_shopee_orders(current_user: User = Depends(get_current_user)):
    # Validate configuration before queueing
    try:
        ShopeeService.from_env(settings.shopee_partner_id, settings.shopee_partner_key, settings.shopee_redirect_url)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc))
    job = queue.enqueue(sync_shopee_orders_task, current_user.tenant_id)
    return {"job_id": job.get_id(), "status": job.get_status()}


@router.post("/tiny/products")
def trigger_tiny_products(current_user: User = Depends(get_current_user)):
    try:
        TinyService.from_env(settings.tiny_api_token)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc))
    job = queue.enqueue(sync_tiny_products_task, current_user.tenant_id)
    return {"job_id": job.get_id(), "status": job.get_status()}


@router.post("/reconcile/bank")
def trigger_reconcile(current_user: User = Depends(get_current_user)):
    job = queue.enqueue(reconcile_bank_transactions_task, current_user.tenant_id)
    return {"job_id": job.get_id(), "status": job.get_status()}
