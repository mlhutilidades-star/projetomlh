#!/usr/bin/env python3
"""
Renovar Access Token (Shopee Open Platform v2)

Endpoint correto: /api/v2/auth/access_token/get
Assinatura: base_string = {partner_id}{path}{timestamp}
Não usa access_token na assinatura.
"""
import os
import sys
import requests
import json
import hmac
import hashlib
import time
from pathlib import Path
from dotenv import load_dotenv

env_path = Path(__file__).parent.parent.parent / ".env"
load_dotenv(env_path)

PARTNER_ID = int(os.getenv("SHOPEE_PARTNER_ID", "2013808"))
PARTNER_KEY = os.getenv("SHOPEE_API_PARTNER_KEY", "")
REFRESH_TOKEN = os.getenv("SHOPEE_REFRESH_TOKEN", "").strip('"').strip()
SHOP_ID = int(os.getenv("SHOPEE_SHOP_ID", "1616902621"))

BASE_URL = "https://partner.shopeemobile.com/api/v2"


def generate_sign_for_auth(path: str, timestamp: int) -> str:
    """Assinatura para endpoints de auth (sem access_token)."""
    if not path.startswith("/api/v2"):
        path = f"/api/v2{path}"
    base_string = f"{PARTNER_ID}{path}{timestamp}"
    return hmac.new(PARTNER_KEY.encode(), base_string.encode(), hashlib.sha256).hexdigest()


def update_env(access_token: str, refresh_token: str | None = None):
    """Atualiza o .env com novos tokens."""
    env_file = env_path
    with open(env_file, "r", encoding="utf-8") as f:
        content = f.read()

    import re
    content = re.sub(r'SHOPEE_ACCESS_TOKEN="[^"]*"', f'SHOPEE_ACCESS_TOKEN="{access_token}"', content)
    if refresh_token:
        content = re.sub(r'SHOPEE_REFRESH_TOKEN="[^"]*"', f'SHOPEE_REFRESH_TOKEN="{refresh_token}"', content)

    with open(env_file, "w", encoding="utf-8") as f:
        f.write(content)


def refresh_access_token():
    """Chama o endpoint de refresh e atualiza o .env."""
    path = "/auth/access_token/get"
    timestamp = int(time.time())
    sign = generate_sign_for_auth(path, timestamp)

    params = {
        "partner_id": PARTNER_ID,
        "timestamp": timestamp,
        "sign": sign,
    }

    body = {
        "refresh_token": REFRESH_TOKEN,
        "shop_id": SHOP_ID,
        "partner_id": PARTNER_ID,
    }

    url = BASE_URL + path
    print(f"🔄 Renovando token via {url}")
    print(f"   Refresh Token: {REFRESH_TOKEN[:10]}...")

    resp = requests.post(url, params=params, json=body, timeout=15)
    try:
        data = resp.json()
    except Exception:
        print(f"   ❌ Erro ao parsear resposta: {resp.text}")
        return False

    print(f"   Status HTTP: {resp.status_code}")
    print(f"   Resposta: {json.dumps(data, indent=2, ensure_ascii=False)}")

    if data.get("error"):
        print(f"   ❌ Erro: {data['error']} - {data.get('message', '')}")
        return False

    access_token = data.get("access_token")
    refresh_token = data.get("refresh_token") or REFRESH_TOKEN
    expire_in = data.get("expire_in")

    if not access_token:
        print("   ❌ Resposta sem access_token")
        return False

    print(f"   ✅ Novo access_token: {access_token[:12]}...")
    if expire_in:
        print(f"   ⏳ Expira em: {expire_in} segundos (~{expire_in//3600}h)")
    if refresh_token and refresh_token != REFRESH_TOKEN:
        print(f"   🔄 Novo refresh_token: {refresh_token[:12]}...")

    update_env(access_token, refresh_token)
    print("   📝 .env atualizado com sucesso")
    return True


if __name__ == "__main__":
    if not REFRESH_TOKEN:
        print("❌ REFRESH_TOKEN não configurado")
        sys.exit(1)

    ok = refresh_access_token()
    sys.exit(0 if ok else 1)
