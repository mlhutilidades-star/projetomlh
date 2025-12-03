"""Script para criar executável standalone do Hub Financeiro usando PyInstaller"""
import subprocess
import sys
from pathlib import Path

def main():
    """Cria executável .exe do launcher usando PyInstaller"""
    
    print("🔧 Instalando PyInstaller...")
    subprocess.run([sys.executable, "-m", "pip", "install", "pyinstaller"], check=True)
    
    print("\n📦 Criando executável...")
    
    # Comando PyInstaller
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--onefile",                          # Arquivo único
        "--windowed",                         # Sem console (comentar se quiser ver logs)
        "--name", "HubFinanceiro",           # Nome do executável
        "--icon", "NONE",                    # Sem ícone (pode adicionar .ico depois)
        "--add-data", "app.py;.",            # Incluir app.py
        "--add-data", "modules;modules",     # Incluir módulos
        "--add-data", "pages;pages",         # Incluir páginas
        "--add-data", "requirements.txt;.",  # Incluir requirements
        "--hidden-import", "streamlit",
        "--hidden-import", "pandas",
        "--hidden-import", "sqlalchemy",
        "--collect-all", "streamlit",
        "launcher.py"
    ]
    
    subprocess.run(cmd, check=True)
    
    print("\n✅ Executável criado com sucesso!")
    print(f"📁 Localização: {Path('dist/HubFinanceiro.exe').absolute()}")
    print("\n⚠️  IMPORTANTE:")
    print("   1. O .exe precisa estar na mesma pasta que:")
    print("      - app.py")
    print("      - modules/")
    print("      - pages/")
    print("      - data/ (será criado automaticamente)")
    print("   2. Copie o .exe de dist/ para a raiz do projeto")
    print("\n💡 Após copiar, basta dar duplo clique em HubFinanceiro.exe")

if __name__ == "__main__":
    main()
