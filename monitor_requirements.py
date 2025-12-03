"""
Monitor de requirements.txt - Auto-instalação de dependências
Monitora alterações no requirements.txt e instala automaticamente novos pacotes.
"""

import os
import sys
import time
import json
import subprocess
import hashlib
from pathlib import Path
from datetime import datetime


class RequirementsMonitor:
    def __init__(self, requirements_file="requirements.txt", state_file="installed_requirements.json", log_file="logs/auto_installer.log"):
        self.requirements_file = Path(requirements_file)
        self.state_file = Path(state_file)
        self.log_file = Path(log_file)
        
        # Criar diretório de logs se não existir
        self.log_file.parent.mkdir(parents=True, exist_ok=True)
        
        self.installed_packages = self._load_state()
        self._log("Sistema de auto-instalação iniciado")
    
    def _log(self, message, level="INFO"):
        """Registra mensagem no log com timestamp."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_line = f"[{timestamp}] [{level}] {message}\n"
        
        try:
            with open(self.log_file, 'a', encoding='utf-8') as f:
                f.write(log_line)
        except Exception as e:
            print(f"[ERRO LOG] Falha ao escrever log: {e}")
        
        # Também exibe no console
        print(f"[{level}] {message}")
        
    def _load_state(self):
        """Carrega o estado de pacotes já instalados."""
        if self.state_file.exists():
            try:
                with open(self.state_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                self._log(f"Erro ao carregar estado: {e}", "WARN")
                return {}
        return {}
    
    def _save_state(self):
        """Salva o estado de pacotes instalados."""
        try:
            with open(self.state_file, 'w', encoding='utf-8') as f:
                json.dump(self.installed_packages, f, indent=2, ensure_ascii=False)
        except Exception as e:
            self._log(f"Falha ao salvar estado: {e}", "ERROR")
    
    def _parse_package_line(self, line):
        """
        Extrai o nome do pacote de uma linha do requirements.txt.
        Retorna None se a linha for inválida (comentário, vazia, etc).
        """
        line = line.strip()
        
        # Ignorar linhas vazias e comentários
        if not line or line.startswith('#'):
            return None
        
        # Remover comentários inline
        if '#' in line:
            line = line.split('#')[0].strip()
        
        # Extrair nome do pacote (antes de ==, >=, <=, ~=, !=, <, >)
        for sep in ['==', '>=', '<=', '~=', '!=', '<', '>']:
            if sep in line:
                package = line.split(sep)[0].strip()
                return package
        
        # Se não tem versão especificada, retorna o nome direto
        return line.strip()
    
    def _get_file_hash(self):
        """Calcula hash do arquivo requirements.txt para detectar mudanças."""
        if not self.requirements_file.exists():
            return None
        
        try:
            with open(self.requirements_file, 'rb') as f:
                return hashlib.md5(f.read()).hexdigest()
        except Exception as e:
            self._log(f"Falha ao calcular hash: {e}", "ERROR")
            return None
    
    def _read_requirements(self):
        """Lê e parseia o arquivo requirements.txt."""
        if not self.requirements_file.exists():
            return []
        
        packages = []
        try:
            with open(self.requirements_file, 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f, 1):
                    package = self._parse_package_line(line)
                    if package:
                        packages.append({
                            'name': package,
                            'line': line.strip(),
                            'line_num': line_num
                        })
        except Exception as e:
            self._log(f"Falha ao ler requirements.txt: {e}", "ERROR")
        
        return packages
    
    def _install_package(self, package_info):
        """Instala um pacote usando pip."""
        package_line = package_info['line']
        package_name = package_info['name']
        
        self._log(f"Instalando: {package_line}", "INFO")
        
        try:
            # Executa pip install
            result = subprocess.run(
                [sys.executable, '-m', 'pip', 'install', package_line],
                capture_output=True,
                text=True,
                timeout=300  # 5 minutos timeout
            )
            
            if result.returncode == 0:
                self._log(f"✓ Pacote instalado com sucesso: {package_name}", "INFO")
                return True
            else:
                self._log(f"Falha ao instalar {package_name}: {result.stderr}", "ERROR")
                return False
                
        except subprocess.TimeoutExpired:
            self._log(f"Timeout ao instalar {package_name}", "ERROR")
            return False
        except Exception as e:
            self._log(f"Exceção ao instalar {package_name}: {e}", "ERROR")
            return False
    
    def check_and_install(self):
        """Verifica novos pacotes e instala se necessário."""
        packages = self._read_requirements()
        
        for pkg_info in packages:
            pkg_name = pkg_info['name']
            pkg_line = pkg_info['line']
            
            # Verifica se já foi instalado
            if pkg_line not in self.installed_packages.values():
                # Novo pacote detectado
                if self._install_package(pkg_info):
                    # Marca como instalado
                    self.installed_packages[pkg_name] = pkg_line
                    self._save_state()
    
    def monitor(self, interval=2):
        """
        Monitora continuamente o arquivo requirements.txt.
        
        Args:
            interval: Intervalo em segundos entre verificações (padrão: 2)
        """
        self._log(f"Iniciando monitoramento de {self.requirements_file}", "INFO")
        self._log(f"Verificando a cada {interval} segundos", "INFO")
        self._log(f"Estado salvo em: {self.state_file}", "INFO")
        self._log(f"Logs em: {self.log_file}", "INFO")
        print("\n🔄 Monitor de requirements.txt ativo")
        print("Pressione Ctrl+C para parar\n")
        
        last_hash = self._get_file_hash()
        
        # Primeira verificação ao iniciar
        self.check_and_install()
        
        try:
            while True:
                time.sleep(interval)
                
                current_hash = self._get_file_hash()
                
                # Se o hash mudou, arquivo foi modificado
                if current_hash != last_hash:
                    self._log(f"Alteração detectada em {self.requirements_file}", "INFO")
                    self.check_and_install()
                    last_hash = current_hash
                    
        except KeyboardInterrupt:
            self._log("Monitoramento interrompido pelo usuário", "INFO")
            self._log(f"Total de pacotes gerenciados: {len(self.installed_packages)}", "INFO")
            print(f"\n✓ Monitor encerrado. Pacotes gerenciados: {len(self.installed_packages)}")
        except Exception as e:
            self._log(f"Erro inesperado no monitor: {e}", "ERROR")
            print(f"\n⚠ Monitor encerrado com erro. Verifique {self.log_file}")


def main():
    """Função principal."""
    monitor = RequirementsMonitor()
    monitor.monitor(interval=2)


if __name__ == "__main__":
    main()
