"""
Gerenciador de tokens Shopee v2
- Armazena access_token/refresh_token e expire_at em arquivo JSON
- Atualiza .env ao renovar
- Faz refresh automático quando faltam <5min

Fluxo de refresh:
  endpoint: /api/v2/auth/access_token/get
  assinatura: base_string = {partner_id}{path}{timestamp}
  key: PARTNER_KEY

Se o refresh falhar (refresh_token inválido ou expirado), instruímos rodar
backend/scripts/obter_token_interativo_novo.py para gerar novos tokens.
"""
from __future__ import annotations
import os, time, json, hmac, hashlib
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parents[2]
ENV_PATH = BASE_DIR / ".env"
CACHE_PATH = Path(__file__).with_name(".shopee_token_cache.json")

load_dotenv(ENV_PATH)

PARTNER_ID = int(os.getenv("SHOPEE_PARTNER_ID", "0") or 0)
PARTNER_KEY = os.getenv("SHOPEE_API_PARTNER_KEY", "")
SHOP_ID = int(os.getenv("SHOPEE_SHOP_ID", "0") or 0)
ACCESS_TOKEN_ENV = (os.getenv("SHOPEE_ACCESS_TOKEN", "") or "").strip('"').strip()
REFRESH_TOKEN_ENV = (os.getenv("SHOPEE_REFRESH_TOKEN", "") or "").strip('"').strip()
BASE_URL = "https://partner.shopeemobile.com/api/v2"

class TokenError(RuntimeError):
    pass

def _read_cache():
    if CACHE_PATH.exists():
        try:
            return json.loads(CACHE_PATH.read_text(encoding="utf-8"))
        except Exception:
            return {}
    return {}

def _write_cache(data: dict):
    CACHE_PATH.write_text(json.dumps(data, indent=2), encoding="utf-8")

def _update_env(access_token: str, refresh_token: str | None = None):
    import re
    content = ENV_PATH.read_text(encoding="utf-8")
    content = re.sub(r'SHOPEE_ACCESS_TOKEN="[^"]*"', f'SHOPEE_ACCESS_TOKEN="{access_token}"', content)
    if refresh_token:
        content = re.sub(r'SHOPEE_REFRESH_TOKEN="[^"]*"', f'SHOPEE_REFRESH_TOKEN="{refresh_token}"', content)
    ENV_PATH.write_text(content, encoding="utf-8")

def _sign(path: str, ts: int) -> str:
    if not path.startswith("/api/v2"):
        path = f"/api/v2{path}"
    base = f"{PARTNER_ID}{path}{ts}"
    return hmac.new(PARTNER_KEY.encode(), base.encode(), hashlib.sha256).hexdigest()

def _refresh(refresh_token: str) -> dict:
    import requests
    path = "/auth/access_token/get"
    ts = int(time.time())
    sign = _sign(path, ts)
    params = {"partner_id": PARTNER_ID, "timestamp": ts, "sign": sign}
    body = {"refresh_token": refresh_token, "shop_id": SHOP_ID, "partner_id": PARTNER_ID}
    resp = requests.post(f"{BASE_URL}{path}", params=params, json=body, timeout=15)
    data = resp.json()
    if data.get("error"):
        raise TokenError(f"Refresh falhou: {data.get('error')} - {data.get('message','')}")
    if "access_token" not in data:
        raise TokenError(f"Refresh falhou: resposta sem access_token: {data}")
    return data

def ensure_access_token(min_valid_seconds: int = 300) -> str:
    """
    Retorna um access_token válido. Faz refresh se expirar em <min_valid_seconds.
    Se refresh falhar, levanta TokenError sugerindo reautorizar.
    """
    cache = _read_cache()
    access_token = cache.get("access_token") or ACCESS_TOKEN_ENV
    refresh_token = cache.get("refresh_token") or REFRESH_TOKEN_ENV
    expires_at = cache.get("expires_at", 0)

    now = int(time.time())
    if access_token and expires_at and expires_at - now > min_valid_seconds:
        return access_token

    if not refresh_token:
        raise TokenError("Refresh token ausente. Reautorize com obter_token_interativo_novo.py")

    data = _refresh(refresh_token)
    access_token = data["access_token"]
    new_refresh = data.get("refresh_token", refresh_token)
    expire_in = data.get("expire_in", 4 * 3600)
    expires_at = now + int(expire_in)

    _write_cache({"access_token": access_token, "refresh_token": new_refresh, "expires_at": expires_at})
    _update_env(access_token, new_refresh)
    return access_token
