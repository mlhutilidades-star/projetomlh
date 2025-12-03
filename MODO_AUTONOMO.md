# 🚀 MLH - Sistema Autônomo com Aider

Sistema completo de desenvolvimento autônomo com monitoramento contínuo de dependências e tarefas.

## 📦 Arquivos Criados

### 1. `monitor_requirements.py`
Monitor inteligente que detecta novas dependências no `requirements.txt` e as instala automaticamente.

**Funcionalidades:**
- ✅ Detecção automática de novos pacotes
- ✅ Instalação via pip sem intervenção
- ✅ Log completo em `logs/auto_installer.log`
- ✅ Estado persistente em `installed_requirements.json`
- ✅ Verificação a cada 2 segundos
- ✅ Tolerante a erros (continua rodando mesmo com falhas)

### 2. `monitor_agent.py`
Monitor de tarefas que detecta atualizações nos arquivos de documentação e dispara o Aider automaticamente.

**Funcionalidades:**
- ✅ Monitora `docs/TODO_AUTONOMO_MLH.md` e `docs/STATUS_AUTONOMO.md`
- ✅ Executa Aider ao detectar mudanças
- ✅ Cooldown de 60 segundos entre execuções
- ✅ Log em `logs/auto_agent.log`
- ✅ Estado persistente em `agent_monitor_state.json`

### 3. `run_with_autoinstall.bat` / `run_with_autoinstall.ps1`
Scripts de inicialização que ativam todo o ecossistema autônomo.

**O que fazem:**
1. ✅ Ativam `.venv-aider`
2. ✅ Iniciam monitor de requirements em janela separada
3. ✅ Iniciam monitor de agente em janela separada
4. ✅ Iniciam Aider principal com flags automáticas

## 🎯 Como Usar

### Opção 1: Windows Batch (Recomendado)
```cmd
run_with_autoinstall.bat
```

### Opção 2: PowerShell
```powershell
.\run_with_autoinstall.ps1
```

## 📋 O Que Acontece Ao Iniciar

```
[1/4] Ativando ambiente virtual .venv-aider...
[2/4] Iniciando monitor de requirements.txt em segundo plano...
      📦 Monitor Requirements (janela separada)
      
[3/4] Iniciando monitor de agente autônomo em segundo plano...
      🤖 Monitor Agent (janela separada)
      
[4/4] Aguardando 3 segundos antes de iniciar Aider principal...

========================================
 ✅ Modo Autônomo MLH INICIADO
========================================

Módulos ativos:
  📦 Monitor de dependências (requirements.txt)
  🤖 Monitor de tarefas (TODO/STATUS)
  🚀 Aider em modo automático

Configuração Aider:
  - Model: gpt-4o
  - Auto-commits: habilitado
  - Watch-files: habilitado
  - Auto-yes: habilitado
```

## 🔄 Fluxo de Trabalho Autônomo

### Cenário 1: Aider Adiciona Dependência
1. Aider edita código e adiciona `import requests`
2. Aider atualiza `requirements.txt` com `requests==2.31.0`
3. **Monitor Requirements** detecta a mudança
4. `pip install requests==2.31.0` é executado automaticamente
5. Log registrado em `logs/auto_installer.log`

### Cenário 2: Você Atualiza TODO
1. Você edita `docs/TODO_AUTONOMO_MLH.md`
2. Adiciona um novo item: "- [ ] Criar módulo de exportação"
3. **Monitor Agent** detecta a mudança
4. Aider é disparado automaticamente (se cooldown expirou)
5. Aider lê o TODO e começa a trabalhar na tarefa

### Cenário 3: Aider Atualiza STATUS
1. Aider completa uma tarefa
2. Atualiza `docs/STATUS_AUTONOMO.md`
3. **Monitor Agent** detecta
4. Nova sessão Aider pode ser iniciada (com cooldown)

## 📊 Logs e Estado

Todos os logs ficam em `/logs/`:
- `auto_installer.log` - Instalações de pacotes
- `auto_agent.log` - Execuções do Aider

Estados persistentes:
- `installed_requirements.json` - Pacotes já instalados
- `agent_monitor_state.json` - Hash dos arquivos e timestamps

## ⚠️ Notas Importantes

1. **Janelas Separadas**: Cada monitor roda em uma janela própria do PowerShell/CMD.
   - Para parar tudo: feche todas as janelas manualmente.
   
2. **Cooldown do Agent**: O monitor de agente tem um cooldown de 60 segundos entre execuções do Aider para evitar loops infinitos.

3. **Tolerância a Erros**: Se `pip install` falhar, o monitor continua rodando e registra o erro no log.

4. **Aider Model**: Configurado para `gpt-4o`. Se quiser usar `gpt-4-turbo` ou outro modelo, edite os arquivos `.bat` e `.ps1`.

## 🛠️ Execução Manual de Componentes

### Apenas Monitor de Requirements
```powershell
& ".venv-aider\Scripts\Activate.ps1"
python monitor_requirements.py
```

### Apenas Monitor de Agent
```powershell
& ".venv-aider\Scripts\Activate.ps1"
python monitor_agent.py
```

### Apenas Aider
```powershell
& ".venv-aider\Scripts\Activate.ps1"
aider --model gpt-4o --yes --auto-commits --watch-files .
```

## 🎓 Exemplos de Uso

### Adicionar Dependência Manualmente
Edite `requirements.txt`:
```
pandas==2.0.0
numpy==1.24.0
```

Em 2 segundos, o monitor instala automaticamente.

### Criar Nova Tarefa para Aider
Edite `docs/TODO_AUTONOMO_MLH.md`:
```markdown
## Próximos Passos
- [ ] Implementar validação de CPF/CNPJ
- [ ] Criar testes unitários para parser PDF
```

O monitor detecta e dispara o Aider (se cooldown permitir).

## 🔧 Troubleshooting

### "Aider não encontrado"
Certifique-se de que aider está instalado:
```powershell
& ".venv-aider\Scripts\Activate.ps1"
pip install aider-chat
aider --version
```

### "Ambiente virtual não encontrado"
Crie o venv primeiro:
```powershell
python -m venv .venv-aider
& ".venv-aider\Scripts\Activate.ps1"
pip install --upgrade pip setuptools wheel
pip install aider-chat
```

### Monitor não detecta mudanças
- Verifique se os arquivos existem
- Veja os logs em `logs/`
- Certifique-se de salvar os arquivos após editar

## 📈 Monitoramento

Para ver o que está acontecendo em tempo real:
```powershell
# Windows PowerShell
Get-Content logs\auto_installer.log -Wait -Tail 20
Get-Content logs\auto_agent.log -Wait -Tail 20
```

## ✅ Checklist de Funcionamento

Após iniciar o sistema, você deve ter:
- [ ] 3 janelas abertas (Requirements Monitor, Agent Monitor, Aider)
- [ ] Arquivos de log sendo criados em `/logs/`
- [ ] Estado persistente em arquivos `.json`
- [ ] Aider respondendo a edições de arquivos

---

**🎉 Pronto! Seu ambiente está 100% autônomo.**

Agora você pode editar código, adicionar tarefas no TODO, e tudo se auto-gerencia:
- Dependências → instalação automática
- Tarefas → Aider executa automaticamente
- Commits → feitos automaticamente pelo Aider

Foque apenas no que importa: definir o que quer fazer! 🚀
