#!/usr/bin/env python3
"""
Obter Shopee Access Token e Shop ID via OAuth
Siga as instruções passo a passo
"""
import webbrowser
import requests
import json
from urllib.parse import urlencode
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading
import time

PARTNER_ID = "2013808"
PARTNER_KEY = "shpk4774635844546f67744c5150584a6e554b454f4a576c514b65734c664952"
REDIRECT_URL = "http://localhost:8888/callback"

auth_code = None
server = None

class CallbackHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        global auth_code
        
        # Extrair código da URL
        query = self.path.split('?')[1] if '?' in self.path else ''
        params = {}
        for param in query.split('&'):
            if '=' in param:
                key, value = param.split('=', 1)
                params[key] = value
        
        auth_code = params.get('code')
        
        if auth_code:
            self.send_response(200)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.end_headers()
            msg = """
            <html>
            <head><title>Sucesso</title></head>
            <body style="font-family: Arial; text-align: center; padding: 50px;">
                <h1>✅ Autorização Concedida!</h1>
                <p>Código de autorização recebido com sucesso.</p>
                <p>Você pode fechar esta aba e voltar ao terminal.</p>
            </body>
            </html>
            """
        else:
            self.send_response(400)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.end_headers()
            msg = """
            <html>
            <head><title>Erro</title></head>
            <body style="font-family: Arial; text-align: center; padding: 50px;">
                <h1>❌ Erro na Autorização</h1>
                <p>Nenhum código de autorização foi recebido.</p>
            </body>
            </html>
            """
        
        self.wfile.write(msg.encode())
    
    def log_message(self, format, *args):
        pass  # Suprimir logs

def start_server():
    global server
    server = HTTPServer(('localhost', 8888), CallbackHandler)
    thread = threading.Thread(target=server.serve_forever)
    thread.daemon = True
    thread.start()
    print("✅ Servidor local iniciado em http://localhost:8888")

def get_auth_url():
    """Gerar URL de autenticação"""
    params = {
        'client_id': PARTNER_ID,
        'response_type': 'code',
        'redirect_uri': REDIRECT_URL,
        'state': 'state123'
    }
    url = f"https://partner.shopeemobile.com/api/v2/oauth/authorize?{urlencode(params)}"
    return url

def exchange_code_for_token(auth_code):
    """Trocar código por access token"""
    print("\n🔄 Trocando código por access token...")
    
    url = "https://partner.shopeemobile.com/api/v2/oauth/token"
    
    payload = {
        'code': auth_code,
        'grant_type': 'authorization_code',
        'partner_id': PARTNER_ID,
        'partner_key': PARTNER_KEY,
        'redirect_uri': REDIRECT_URL
    }
    
    try:
        response = requests.post(url, json=payload, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if 'access_token' in data:
                return data['access_token'], data.get('refresh_token')
            else:
                print(f"❌ Erro: {data}")
                return None, None
        else:
            print(f"❌ Erro HTTP {response.status_code}: {response.text}")
            return None, None
    except Exception as e:
        print(f"❌ Erro na requisição: {e}")
        return None, None

def get_shop_id(access_token):
    """Obter Shop ID usando o access token"""
    print("\n🏪 Obtendo Shop ID...")
    
    url = "https://partner.shopeemobile.com/api/v2/shop/get_shop_info"
    
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }
    
    params = {
        'partner_id': PARTNER_ID,
        'access_token': access_token
    }
    
    try:
        response = requests.get(url, params=params, headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if 'data' in data:
                shop_id = data['data'].get('shop_id')
                shop_name = data['data'].get('shop_name')
                return shop_id, shop_name
            else:
                print(f"❌ Erro: {data}")
                return None, None
        else:
            print(f"❌ Erro HTTP {response.status_code}: {response.text}")
            return None, None
    except Exception as e:
        print(f"❌ Erro na requisição: {e}")
        return None, None

def main():
    print("\n" + "="*70)
    print("🔐 OBTENDO SHOPEE ACCESS TOKEN E SHOP ID")
    print("="*70)
    
    print("\n📋 Pré-requisitos:")
    print("  ✅ Partner ID: 2013808")
    print("  ✅ Partner Key: Configurada")
    print("  ✅ Redirect URL: http://localhost:8888/callback")
    
    print("\n" + "-"*70)
    print("PASSO 1: Iniciando servidor local...")
    print("-"*70)
    
    start_server()
    time.sleep(1)
    
    print("\n" + "-"*70)
    print("PASSO 2: Gerando URL de autenticação...")
    print("-"*70)
    
    auth_url = get_auth_url()
    print(f"\n🔗 URL de autenticação gerada:")
    print(f"   {auth_url}")
    
    print("\n" + "-"*70)
    print("PASSO 3: Abrindo navegador para autenticação...")
    print("-"*70)
    
    print("\n⏳ Abrindo navegador em 2 segundos...")
    time.sleep(2)
    
    try:
        webbrowser.open(auth_url)
        print("✅ Navegador aberto")
    except:
        print("⚠️  Não consegui abrir o navegador automaticamente")
        print(f"   Abra manualmente: {auth_url}")
    
    print("\n" + "-"*70)
    print("PASSO 4: Aguardando autorização do Shopee...")
    print("-"*70)
    
    print("\n⏳ Aguardando callback (máximo 5 minutos)...")
    
    # Aguardar código
    timeout = 300  # 5 minutos
    start_time = time.time()
    
    while auth_code is None and (time.time() - start_time) < timeout:
        time.sleep(1)
    
    if auth_code is None:
        print("\n❌ Timeout: Nenhuma autorização recebida em 5 minutos")
        return
    
    print(f"✅ Código de autorização recebido: {auth_code[:20]}...")
    
    print("\n" + "-"*70)
    print("PASSO 5: Trocando código por Access Token...")
    print("-"*70)
    
    access_token, refresh_token = exchange_code_for_token(auth_code)
    
    if not access_token:
        print("\n❌ Não foi possível obter o Access Token")
        return
    
    print(f"✅ Access Token obtido: {access_token[:30]}...")
    if refresh_token:
        print(f"✅ Refresh Token obtido: {refresh_token[:30]}...")
    
    print("\n" + "-"*70)
    print("PASSO 6: Obtendo Shop ID...")
    print("-"*70)
    
    shop_id, shop_name = get_shop_id(access_token)
    
    if not shop_id:
        print("\n❌ Não foi possível obter o Shop ID")
        return
    
    print(f"✅ Shop ID obtido: {shop_id}")
    print(f"✅ Nome da loja: {shop_name}")
    
    print("\n" + "="*70)
    print("✅ SUCESSO! COPIE ESTES VALORES:")
    print("="*70)
    
    print(f"\nSHOPEE_ACCESS_TOKEN={access_token}")
    print(f"SHOPEE_SHOP_ID={shop_id}")
    
    print("\n" + "-"*70)
    print("📝 PRÓXIMAS AÇÕES:")
    print("-"*70)
    print("\n1. Abra o arquivo: ap-gestor-saas/.env")
    print("\n2. Preencha as linhas:")
    print(f"   SHOPEE_ACCESS_TOKEN={access_token}")
    print(f"   SHOPEE_SHOP_ID={shop_id}")
    print("\n3. Salve o arquivo")
    print("\n4. Execute os scripts de sincronização:")
    print("   docker-compose exec backend python scripts/sync_tiny_real.py")
    print("   docker-compose exec backend python scripts/sync_shopee_real.py")
    
    print("\n" + "="*70 + "\n")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n❌ Interrompido pelo usuário")
    except Exception as e:
        print(f"\n❌ Erro: {e}")
    finally:
        if server:
            server.shutdown()
