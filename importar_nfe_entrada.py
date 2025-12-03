#!/usr/bin/env python3
"""
Script para importar NF-e de entrada no Tiny via API.
Lê o XML local, envia para o endpoint incluir.xml.php com tipo E (entrada).
"""
import json
import pathlib
import sys
import urllib.request
import urllib.parse
from datetime import datetime

# Configurações
ENV_PATH = pathlib.Path(__file__).parent / '.env'
XML_PATH = pathlib.Path(__file__).parent / 'logs' / 'nfe_ajustada_20251203-080511.xml'
API_URL = 'https://api.tiny.com.br/api2/incluir.nota.xml.php'

def read_token():
    """Lê TINY_API_TOKEN do .env"""
    if not ENV_PATH.exists():
        print(f"❌ Arquivo .env não encontrado em {ENV_PATH}")
        sys.exit(1)
    
    for line in ENV_PATH.read_text(encoding='utf-8').splitlines():
        stripped = line.strip()
        if stripped.startswith('TINY_API_TOKEN='):
            token = stripped.split('=', 1)[1].strip().strip('"').strip("'")
            if token:
                return token
    
    print("❌ TINY_API_TOKEN não encontrado no .env")
    sys.exit(1)

def read_xml():
    """Lê o XML da NF-e"""
    if not XML_PATH.exists():
        print(f"❌ XML não encontrado em {XML_PATH}")
        sys.exit(1)
    
    return XML_PATH.read_text(encoding='utf-8')

def enviar_nfe_entrada(token, xml_content):
    """
    Envia NF-e para o Tiny via importação de XML.
    O Tiny detecta automaticamente se é entrada/saída pelo XML.
    
    Parâmetros:
    - token: token de API
    - xml_content: conteúdo completo do XML
    """
    print(f"📤 Enviando NF-e para {API_URL}...")
    
    # Monta payload conforme documentação Tiny
    # Não precisa informar tipo - o Tiny detecta pelo XML
    params = {
        'token': token,
        'xml': xml_content,
        'lancarEstoque': 'S',  # Lança estoque automaticamente
        'lancarContas': 'N'     # Não lança contas (só queremos atualizar custo)
    }
    
    data = urllib.parse.urlencode(params).encode('utf-8')
    req = urllib.request.Request(API_URL, data=data, method='POST')
    
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            response_text = resp.read().decode('utf-8')
            
            # Debug: mostra resposta raw
            print(f"\n[DEBUG] Resposta raw ({len(response_text)} bytes):")
            print(response_text[:500])
            print()
            
            response = json.loads(response_text)
            
            retorno = response.get('retorno', {})
            status = retorno.get('status')
            
            print("\n" + "="*60)
            print("RESPOSTA DA API TINY")
            print("="*60)
            print(json.dumps(response, indent=2, ensure_ascii=False))
            print("="*60 + "\n")
            
            if status == 'OK':
                id_nota = retorno.get('idNotaFiscal')
                if id_nota:
                    print(f"✅ NF-e importada com sucesso!")
                    print(f"   ID: {id_nota}")
                    print(f"\n💡 Próximos passos:")
                    print(f"   1. Acesse Tiny → Compras → Notas Fiscais")
                    print(f"   2. Localize a nota ID {id_nota}")
                    print(f"   3. O estoque já foi lançado automaticamente")
                    print(f"   4. O custo dos produtos foi atualizado")
                else:
                    print("✅ Status OK, mas ID da nota não retornado")
            else:
                print(f"❌ Erro ao importar NF-e")
                erros = retorno.get('erros', [])
                codigo_erro = retorno.get('codigo_erro')
                
                if codigo_erro:
                    print(f"   Código: {codigo_erro}")
                
                for erro_item in erros:
                    erro_msg = erro_item.get('erro', '')
                    print(f"   • {erro_msg}")
                
                # Salva log de erro
                log_dir = pathlib.Path(__file__).parent / 'logs'
                log_dir.mkdir(exist_ok=True)
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                log_path = log_dir / f'erro_importacao_entrada_{timestamp}.json'
                log_path.write_text(json.dumps(response, indent=2, ensure_ascii=False), encoding='utf-8')
                print(f"\n📝 Log completo salvo em: {log_path}")
            
            return response
            
    except urllib.error.HTTPError as e:
        print(f"❌ Erro HTTP {e.code}: {e.reason}")
        try:
            error_body = e.read().decode('utf-8')
            print(f"   Resposta: {error_body}")
        except:
            pass
        sys.exit(1)
    except Exception as e:
        print(f"❌ Erro inesperado: {e}")
        sys.exit(1)

def main():
    print("🚀 Importador de NF-e de Entrada - Tiny API")
    print("="*60)
    
    # Lê credenciais e XML
    token = read_token()
    xml_content = read_xml()
    
    print(f"✓ Token carregado do .env")
    print(f"✓ XML carregado: {XML_PATH.name}")
    print(f"✓ Tamanho: {len(xml_content):,} bytes")
    
    # Extrai chave de acesso para referência
    if 'chNFe' in xml_content:
        import re
        match = re.search(r'<chNFe>(\d{44})</chNFe>', xml_content)
        if match:
            chave = match.group(1)
            print(f"✓ Chave: {chave}")
    
    print("\n⚠️  ATENÇÃO:")
    print("   Esta operação importará a NF-e no Tiny.")
    print("   O Tiny detectará automaticamente se é entrada ou saída.")
    print("   Certifique-se de que a nota anterior foi cancelada na SEFAZ.\n")
    
    # Aguarda confirmação
    try:
        resposta = input("Continuar? (s/N): ").strip().lower()
        if resposta != 's':
            print("❌ Operação cancelada pelo usuário")
            sys.exit(0)
    except KeyboardInterrupt:
        print("\n❌ Operação cancelada")
        sys.exit(0)
    
    # Envia para API
    enviar_nfe_entrada(token, xml_content)

if __name__ == '__main__':
    main()
