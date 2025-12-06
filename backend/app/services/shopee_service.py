from __future__ import annotations

from dataclasses import dataclass


@dataclass
class ShopeeService:
    partner_id: str
    partner_key: str
    redirect_url: str

    @staticmethod
    def from_env(partner_id: str | None, partner_key: str | None, redirect_url: str | None) -> "ShopeeService":
        if not partner_id or not partner_key or not redirect_url:
            raise ValueError("Shopee credentials are not fully configured")
        return ShopeeService(partner_id=str(partner_id), partner_key=partner_key, redirect_url=redirect_url)

    def sync_orders(self, tenant_id: int) -> dict[str, str]:
        # Placeholder for real Shopee API call; currently just acknowledges configuration.
        masked_key = f"{self.partner_key[:4]}...{self.partner_key[-4:]}" if len(self.partner_key) >= 8 else "***"
        return {
            "status": "ok",
            "message": f"Shopee sync configured for tenant {tenant_id}",
            "partner_id": self.partner_id,
            "partner_key_masked": masked_key,
            "redirect_url": self.redirect_url,
        }
