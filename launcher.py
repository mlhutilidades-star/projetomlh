"""Launcher do Hub Financeiro - Inicia o Streamlit automaticamente"""
import subprocess
import sys
import os
import time
import webbrowser
from pathlib import Path

def main():
    """Inicia o servidor Streamlit e abre o navegador automaticamente"""
    # Garantir que está no diretório correto
    script_dir = Path(__file__).parent
    os.chdir(script_dir)
    
    # Verificar se está no ambiente virtual
    venv_python = script_dir / "venv" / "Scripts" / "python.exe"
    if not venv_python.exists():
        print("❌ Ambiente virtual não encontrado!")
        print(f"   Esperado em: {venv_python}")
        print("\nCrie o ambiente virtual primeiro com:")
        print("   python -m venv venv")
        print("   .\\venv\\Scripts\\Activate.ps1")
        print("   pip install -r requirements.txt")
        input("\nPressione ENTER para sair...")
        sys.exit(1)
    
    # URL do Streamlit
    url = "http://localhost:8501"
    
    print("🚀 Iniciando Hub Financeiro...")
    print(f"📂 Diretório: {script_dir}")
    print(f"🐍 Python: {venv_python}")
    print(f"🌐 URL: {url}")
    print("\n⏳ Aguardando servidor inicializar...\n")
    
    # Iniciar Streamlit em background
    processo = subprocess.Popen(
        [str(venv_python), "-m", "streamlit", "run", "app.py", 
         "--server.headless", "true",
         "--browser.gatherUsageStats", "false"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0
    )
    
    # Aguardar servidor inicializar (timeout 15s)
    max_attempts = 30
    for i in range(max_attempts):
        try:
            import urllib.request
            urllib.request.urlopen(url, timeout=1)
            print("✅ Servidor iniciado com sucesso!")
            break
        except:
            time.sleep(0.5)
            if i % 4 == 0:
                print(f"   Tentativa {i//4 + 1}/{max_attempts//4}...")
    else:
        print("⚠️  Timeout ao aguardar servidor. Abrindo navegador mesmo assim...")
    
    # Abrir navegador
    print(f"🌐 Abrindo navegador em {url}...")
    webbrowser.open(url)
    
    print("\n" + "="*60)
    print("✨ HUB FINANCEIRO RODANDO ✨")
    print("="*60)
    print(f"\n📊 Acesse: {url}")
    print("\n⚠️  NÃO FECHE ESTA JANELA!")
    print("   O sistema está rodando aqui.\n")
    print("Para encerrar: pressione Ctrl+C ou feche esta janela.\n")
    
    try:
        # Manter processo rodando
        processo.wait()
    except KeyboardInterrupt:
        print("\n\n🛑 Encerrando servidor...")
        processo.terminate()
        processo.wait()
        print("✅ Servidor encerrado.")

if __name__ == "__main__":
    main()
