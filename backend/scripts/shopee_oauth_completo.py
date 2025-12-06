import hmac
import hashlib
import time
import json
import threading
import webbrowser
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs, urlencode

import requests

# =========================
# CONFIGURAÇÕES DO SEU APP
# =========================

PARTNER_ID = 2013808
PARTNER_KEY = "shpk4774635844546f67744c5150584a6e554b454f4a576c514b65734c664952"
REDIRECT_URL = "https://lynette-semiexpositive-broadly.ngrok-free.dev/callback"

# Em muitos casos a Shopee envia shop_id no callback (?shop_id=...),
# mas, se quiser forçar, pode usar o SHOP_ID fixo abaixo:
DEFAULT_SHOP_ID = 1616902621  # opcional; usamos só se não vier no callback

# Endpoints típicos (ajuste se necessário para o seu ambiente/região)
AUTH_BASE_URL = "https://partner.shopeemobile.com/api/v2/shop/auth_partner"
TOKEN_URL = "https://partner.shopeemobile.com/api/v2/auth/token/get"

# Caminhos usados na base_string do HMAC (devem bater com a URL)
PATH_AUTH = "/api/v2/shop/auth_partner"
PATH_TOKEN = "/api/v2/auth/token/get"

# Porta onde o servidor local vai ouvir (ngrok deve apontar para ela)
LOCAL_SERVER_PORT = 8000
CALLBACK_PATH = "/callback"


# =========================
# FUNÇÃO DE ASSINATURA HMAC
# =========================

def generate_sign(partner_id: int, path: str, timestamp: int, partner_key: str) -> str:
    """
    Gera HMAC-SHA256 em hex:
    base_string = f"{partner_id}{path}{timestamp}"
    key = partner_key
    """
    base_string = f"{partner_id}{path}{timestamp}"
    digest = hmac.new(
        partner_key.encode("utf-8"),
        base_string.encode("utf-8"),
        hashlib.sha256
    ).hexdigest()
    return digest


# =========================
# SERVIDOR HTTP PARA CALLBACK
# =========================

class OAuthCallbackHandler(BaseHTTPRequestHandler):
    """
    Handler para /callback que captura ?code=...&shop_id=...
    e sinaliza a thread principal imediatamente.
    """
    auth_code = None
    shop_id = None
    state = None
    event = threading.Event()

    def do_GET(self):
        parsed = urlparse(self.path)

        if parsed.path != CALLBACK_PATH:
            self.send_response(404)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.end_headers()
            self.wfile.write(b"Not found")
            return

        query = parse_qs(parsed.query)
        code = query.get("code", [None])[0]
        shop_id = query.get("shop_id", [None])[0]
        state = query.get("state", [None])[0]

        if not code:
            self.send_response(400)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.end_headers()
            self.wfile.write(b"Missing 'code' in query params")
            return

        # Guarda os dados em variáveis de classe
        OAuthCallbackHandler.auth_code = code
        OAuthCallbackHandler.shop_id = shop_id
        OAuthCallbackHandler.state = state
        OAuthCallbackHandler.event.set()  # avisa a thread principal

        # Resposta amigável pro navegador
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        response_html = """
        <html>
          <head><title>Shopee OAuth</title></head>
          <body>
            <h1>Autorizacao concluida</h1>
            <p>Voce ja pode fechar esta aba e voltar para o terminal.</p>
          </body>
        </html>
        """
        self.wfile.write(response_html.encode("utf-8"))

    # Evita log poluindo o terminal
    def log_message(self, format, *args):
        return


def start_local_server():
    """
    Sobe o HTTPServer em thread separada para receber o callback.
    """
    server_address = ("0.0.0.0", LOCAL_SERVER_PORT)
    httpd = HTTPServer(server_address, OAuthCallbackHandler)

    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    return httpd


# =========================
# FLUXO OAUTH
# =========================

def generate_authorization_url(state: str) -> str:
    """
    Gera URL de autorização para Shopee.
    Aqui usamos:
      - partner_id
      - redirect
      - timestamp
      - sign (HMAC)
      - state
      - (opcional) response_type=code

    Ajuste os parâmetros conforme a documentação da sua região se necessário.
    """
    timestamp = int(time.time())
    sign = generate_sign(PARTNER_ID, PATH_AUTH, timestamp, PARTNER_KEY)

    params = {
        "partner_id": PARTNER_ID,
        "redirect": REDIRECT_URL,
        "timestamp": timestamp,
        "sign": sign,
        "state": state,
        "response_type": "code",  # se a doc não usar, remova
    }

    return AUTH_BASE_URL + "?" + urlencode(params)


def exchange_code_for_tokens(code: str, shop_id):
    """
    Troca o authorization code por access_token e refresh_token.

    Usa:
      - POST TOKEN_URL
      - Assinatura HMAC com base_string = "{partner_id}{path}{timestamp}"
      - query params: partner_id, timestamp, sign
      - body JSON: partner_id, shop_id, code
    """
    timestamp = int(time.time())
    sign = generate_sign(PARTNER_ID, PATH_TOKEN, timestamp, PARTNER_KEY)

    # Se não vier shop_id no callback, usa o default que você já conhece
    if shop_id is None:
        print("⚠️ shop_id não veio no callback, usando DEFAULT_SHOP_ID.")
        shop_id = DEFAULT_SHOP_ID

    params = {
        "partner_id": PARTNER_ID,
        "timestamp": timestamp,
        "sign": sign,
    }

    payload = {
        "partner_id": PARTNER_ID,
        "shop_id": int(shop_id),
        "code": code,
    }

    print("\n🔄 Trocando authorization code por tokens na Shopee...")
    response = requests.post(TOKEN_URL, params=params, json=payload, timeout=10)

    try:
        data = response.json()
    except Exception:
        print("❌ Erro ao decodificar JSON da resposta:")
        print(response.text)
        raise

    if response.status_code != 200:
        print(f"❌ HTTP {response.status_code} na troca de token:")
        print(json.dumps(data, indent=2, ensure_ascii=False))
        raise SystemExit(1)

    # Aqui esperamos algo no formato:
    # {"access_token":"XXX","refresh_token":"YYY","expire_in":14400,...}
    print("\n✅ Resposta da Shopee:")
    print(json.dumps(data, indent=2, ensure_ascii=False))

    access_token = data.get("access_token")
    refresh_token = data.get("refresh_token")

    print("\n==================== TOKENS OBTIDOS ====================")
    print(f"access_token : {access_token}")
    print(f"refresh_token: {refresh_token}")
    print("========================================================")
    
    print("\n📝 Atualize o .env:")
    print(f'SHOPEE_ACCESS_TOKEN="{access_token}"')
    print(f'SHOPEE_REFRESH_TOKEN="{refresh_token}"')

    # Retorna tudo caso queira usar programaticamente
    return data


def main():
    print("=== SHOPEE OAUTH 2.0 FLOW (code -> access_token) ===\n")

    # 1) Sobe servidor local para capturar o callback
    httpd = start_local_server()
    print(f"🌐 Servidor local ouvindo em http://localhost:{LOCAL_SERVER_PORT}{CALLBACK_PATH}")

    # 2) Gera state aleatório (poderia ser mais robusto, tipo uuid4)
    state = f"shopee_state_{int(time.time())}"

    # 3) Gera URL de autorização
    auth_url = generate_authorization_url(state)
    print("\n🔗 URL de autorização gerada:")
    print(auth_url)

    # 4) Abre navegador automaticamente
    print("\n🌍 Abrindo navegador para autorização...")
    webbrowser.open(auth_url)

    print("\n⚠️ Se o navegador não abrir, copie e cole a URL acima manualmente.")
    print("⏳ Aguardando callback da Shopee (authorization code)...\n")

    # 5) Espera o callback (por ex. 300s)
    if not OAuthCallbackHandler.event.wait(timeout=300):
        print("❌ Timeout esperando o callback. Verifique se o ngrok está apontando para esta máquina/porta.")
        httpd.shutdown()
        return

    # Desliga o servidor após receber o callback
    httpd.shutdown()

    code = OAuthCallbackHandler.auth_code
    shop_id = OAuthCallbackHandler.shop_id
    received_state = OAuthCallbackHandler.state

    print("✅ Callback recebido!")
    print(f"code   = {code}")
    print(f"shop_id= {shop_id}")
    print(f"state  = {received_state}")

    # (opcional) validar state
    if received_state and received_state != state:
        print("⚠️ Atenção: 'state' recebido é diferente do enviado. Possível CSRF.")
        # Você pode abortar aqui se quiser.
        # return

    # 6) IMEDIATAMENTE trocar o code por tokens
    exchange_code_for_tokens(code, shop_id)


if __name__ == "__main__":
    main()
