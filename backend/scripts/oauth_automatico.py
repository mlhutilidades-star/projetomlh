#!/usr/bin/env python3
"""
OAuth automático - Captura callback e troca por token imediatamente
"""
import requests
import hmac
import hashlib
import time
import webbrowser
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

PARTNER_ID = "2013808"
PARTNER_KEY = "shpk4774635844546f67744c5150584a6e554b454f4a576c514b65734c664952"
SHOP_ID = "1616902621"
REDIRECT_URL = "http://localhost:8000/callback"

# Variável global para armazenar o code
received_code = None

class CallbackHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        global received_code
        
        # Parse da URL
        parsed = urlparse(self.path)
        params = parse_qs(parsed.query)
        
        if 'code' in params:
            received_code = params['code'][0]
            
            # Responder ao navegador
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            html = """
                <html>
                <body style="font-family: Arial; text-align: center; padding: 50px;">
                    <h1 style="color: green;">Autorizacao recebida!</h1>
                    <p>Voce pode fechar esta janela.</p>
                </body>
                </html>
            """
            self.wfile.write(html.encode('utf-8'))
        else:
            self.send_response(400)
            self.send_header('Content-type', 'text/plain')
            self.end_headers()
            self.wfile.write(b'Code not found')
    
    def log_message(self, format, *args):
        pass  # Silenciar logs

def generate_sign(path, timestamp):
    base_string = f"{PARTNER_ID}{path}{timestamp}"
    return hmac.new(
        PARTNER_KEY.encode(),
        base_string.encode(),
        hashlib.sha256
    ).hexdigest()

def exchange_code_for_token(code):
    """Trocar code por access token"""
    path = "/api/v2/auth/token/get"
    timestamp = int(time.time())
    sign = generate_sign(path, timestamp)
    
    url = f"https://partner.shopeemobile.com{path}"
    params = {
        "partner_id": PARTNER_ID,
        "timestamp": timestamp,
        "sign": sign
    }
    
    body = {
        "code": code,
        "shop_id": int(SHOP_ID),
        "partner_id": int(PARTNER_ID)
    }
    
    response = requests.post(url, params=params, json=body)
    return response

print("="*70)
print("🔐 OAUTH AUTOMÁTICO - SHOPEE")
print("="*70)

# Criar URL de autorização
auth_url = f"https://partner.shopeemobile.com/api/v2/oauth/authorize?partner_id={PARTNER_ID}&response_type=code&redirect_uri={REDIRECT_URL}&state=state123"

print(f"\n1️⃣  Abrindo navegador para autorização...")
print(f"   URL: {auth_url}")

# Abrir navegador
webbrowser.open(auth_url)

print(f"\n2️⃣  Aguardando callback em {REDIRECT_URL}...")
print(f"   Autorize a aplicação no navegador.")

# Iniciar servidor HTTP local
server = HTTPServer(('localhost', 8000), CallbackHandler)

# Aguardar 1 requisição
server.handle_request()

if received_code:
    print(f"\n3️⃣  ✅ Code recebido: {received_code}")
    print(f"\n4️⃣  🔄 Trocando por access token...")
    
    response = exchange_code_for_token(received_code)
    
    print(f"\n📥 Resposta:")
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        if "access_token" in data:
            print(f"\n✅ SUCESSO!")
            print(f"\nACCESS_TOKEN: {data['access_token']}")
            print(f"REFRESH_TOKEN: {data['refresh_token']}")
            print(f"EXPIRE_IN: {data.get('expire_in', 'N/A')} segundos")
            
            print(f"\n📝 Atualize o .env:")
            print(f'SHOPEE_ACCESS_TOKEN="{data["access_token"]}"')
            print(f'SHOPEE_REFRESH_TOKEN="{data["refresh_token"]}"')
        else:
            print(f"\n❌ Erro: {data}")
    else:
        print(f"Body: {response.text}")
        print(f"\n❌ Falha na requisição")
else:
    print(f"\n❌ Code não recebido")
