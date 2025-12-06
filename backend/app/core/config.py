from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    api_v1_prefix: str = "/api/v1"
    project_name: str = "AP Gestor Seller"

    database_url: str = "postgresql+psycopg2://postgres:postgres@db:5432/ap_gestor"
    redis_url: str = "redis://redis:6379/0"

    jwt_secret_key: str = "changeme"
    jwt_refresh_secret_key: str = "changeme_refresh"
    access_token_expire_minutes: int = 30
    refresh_token_expire_minutes: int = 60 * 24 * 7

    # Admin seed
    admin_email: str = "admin@example.com"
    admin_password: str = "admin123"
    admin_tenant: str = "Default Tenant"

    # Integrations
    tiny_api_token: str | None = None
    shopee_partner_id: str | None = None
    shopee_partner_key: str | None = None
    shopee_redirect_url: str | None = None

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


@lru_cache
def get_settings() -> Settings:
    return Settings()
