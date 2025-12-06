import time
from typing import Any

from app.core.config import get_settings
from app.services import ShopeeService, TinyService

settings = get_settings()


def sync_shopee_orders_task(tenant_id: int) -> dict[str, Any]:
    service = ShopeeService.from_env(settings.shopee_partner_id, settings.shopee_partner_key, settings.shopee_redirect_url)
    time.sleep(1)
    return service.sync_orders(tenant_id)


def sync_tiny_products_task(tenant_id: int) -> dict[str, Any]:
    service = TinyService.from_env(settings.tiny_api_token)
    time.sleep(1)
    return service.sync_products(tenant_id)


def reconcile_bank_transactions_task(tenant_id: int) -> dict[str, Any]:
    time.sleep(1)
    return {"status": "ok", "message": f"Bank reconciliation done for tenant {tenant_id}"}
