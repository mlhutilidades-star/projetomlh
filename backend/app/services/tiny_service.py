from __future__ import annotations

from dataclasses import dataclass


@dataclass
class TinyService:
    token: str

    @staticmethod
    def from_env(token: str | None) -> "TinyService":
        if not token:
            raise ValueError("Tiny API token is not configured")
        return TinyService(token=token)

    def sync_products(self, tenant_id: int) -> dict[str, str]:
        # Placeholder for real Tiny API call; currently just acknowledges configuration.
        return {
            "status": "ok",
            "message": f"Tiny sync configured for tenant {tenant_id}",
            "token_last4": self.token[-4:],
        }
