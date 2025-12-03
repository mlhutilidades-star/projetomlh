"""
Monitor de Agente Autônomo - MLH
Monitora arquivos TODO e STATUS, executa Aider automaticamente quando detectar atualizações.
"""

import os
import sys
import time
import json
import subprocess
import hashlib
from pathlib import Path
from datetime import datetime


class AgentMonitor:
    def __init__(self, 
                 todo_file="docs/TODO_AUTONOMO_MLH.md",
                 status_file="docs/STATUS_AUTONOMO.md",
                 state_file="agent_monitor_state.json",
                 log_file="logs/auto_agent.log"):
        
        self.todo_file = Path(todo_file)
        self.status_file = Path(status_file)
        self.state_file = Path(state_file)
        self.log_file = Path(log_file)
        
        # Criar diretório de logs se não existir
        self.log_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Estado: armazena hash dos arquivos e timestamp da última execução
        self.state = self._load_state()
        self.aider_process = None
        
        self._log("Monitor de agente autônomo iniciado")
    
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
        """Carrega o estado do monitor."""
        if self.state_file.exists():
            try:
                with open(self.state_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                self._log(f"Erro ao carregar estado: {e}", "WARN")
                return {}
        return {}
    
    def _save_state(self):
        """Salva o estado do monitor."""
        try:
            with open(self.state_file, 'w', encoding='utf-8') as f:
                json.dump(self.state, f, indent=2, ensure_ascii=False)
        except Exception as e:
            self._log(f"Falha ao salvar estado: {e}", "ERROR")
    
    def _get_file_hash(self, filepath):
        """Calcula hash de um arquivo."""
        if not filepath.exists():
            return None
        
        try:
            with open(filepath, 'rb') as f:
                return hashlib.md5(f.read()).hexdigest()
        except Exception as e:
            self._log(f"Falha ao calcular hash de {filepath}: {e}", "ERROR")
            return None
    
    def _check_for_updates(self):
        """Verifica se houve atualizações nos arquivos monitorados."""
        updated = False
        
        # Verifica TODO
        todo_hash = self._get_file_hash(self.todo_file)
        if todo_hash and todo_hash != self.state.get('todo_hash'):
            self._log(f"Atualização detectada em {self.todo_file}", "INFO")
            self.state['todo_hash'] = todo_hash
            updated = True
        
        # Verifica STATUS
        status_hash = self._get_file_hash(self.status_file)
        if status_hash and status_hash != self.state.get('status_hash'):
            self._log(f"Atualização detectada em {self.status_file}", "INFO")
            self.state['status_hash'] = status_hash
            updated = True
        
        return updated
    
    def _should_run_aider(self):
        """Verifica se deve executar o Aider (evita execuções duplicadas)."""
        last_run = self.state.get('last_aider_run', 0)
        current_time = time.time()
        
        # Evita executar mais de uma vez a cada 60 segundos
        if current_time - last_run < 60:
            self._log("Aider executado recentemente, aguardando cooldown", "INFO")
            return False
        
        return True
    
    def _run_aider(self):
        """Executa o Aider em modo automático."""
        if not self._should_run_aider():
            return
        
        self._log("Iniciando Aider em modo automático", "INFO")
        
        try:
            # Comando Aider
            cmd = [
                "aider",
                "--model", "gpt-4o",
                "--yes",
                "--auto-commits",
                "--watch-files", "."
            ]
            
            self._log(f"Comando: {' '.join(cmd)}", "INFO")
            
            # Executa Aider (modo interativo, não captura output)
            self.aider_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # Atualiza timestamp
            self.state['last_aider_run'] = time.time()
            self._save_state()
            
            self._log("Aider iniciado com sucesso", "INFO")
            
            # Aguarda um pouco para verificar se não houve erro imediato
            time.sleep(5)
            
            if self.aider_process.poll() is not None:
                # Processo terminou rapidamente, provavelmente erro
                stdout, stderr = self.aider_process.communicate()
                self._log(f"Aider terminou rapidamente. Stderr: {stderr}", "ERROR")
            
        except FileNotFoundError:
            self._log("Aider não encontrado. Verifique se está instalado e no PATH.", "ERROR")
        except Exception as e:
            self._log(f"Erro ao executar Aider: {e}", "ERROR")
    
    def monitor(self, interval=2):
        """
        Monitora continuamente os arquivos TODO e STATUS.
        
        Args:
            interval: Intervalo em segundos entre verificações (padrão: 2)
        """
        self._log(f"Monitorando: {self.todo_file} e {self.status_file}", "INFO")
        self._log(f"Verificando a cada {interval} segundos", "INFO")
        self._log(f"Logs em: {self.log_file}", "INFO")
        print("\n🤖 Monitor de agente autônomo ativo")
        print("Pressione Ctrl+C para parar\n")
        
        # Primeira verificação e inicialização de hashes
        if not self.state.get('todo_hash'):
            self.state['todo_hash'] = self._get_file_hash(self.todo_file)
        if not self.state.get('status_hash'):
            self.state['status_hash'] = self._get_file_hash(self.status_file)
        self._save_state()
        
        try:
            while True:
                time.sleep(interval)
                
                # Verifica atualizações
                if self._check_for_updates():
                    self._log("Mudanças detectadas, avaliando execução do Aider", "INFO")
                    self._run_aider()
                    self._save_state()
                    
        except KeyboardInterrupt:
            self._log("Monitor interrompido pelo usuário", "INFO")
            print("\n✓ Monitor de agente encerrado")
            
            # Encerra Aider se estiver rodando
            if self.aider_process and self.aider_process.poll() is None:
                self._log("Encerrando processo Aider", "INFO")
                self.aider_process.terminate()
                
        except Exception as e:
            self._log(f"Erro inesperado no monitor: {e}", "ERROR")
            print(f"\n⚠ Monitor encerrado com erro. Verifique {self.log_file}")


def main():
    """Função principal."""
    monitor = AgentMonitor()
    monitor.monitor(interval=2)


if __name__ == "__main__":
    main()
