# Como Criar Atalho no Desktop

## Opção 1: Launcher Python com Auto-Open (Recomendado)

### Usando o Batch File (Mais Simples)
1. Clique com botão direito em `Iniciar_Hub_Financeiro.bat`
2. Selecione "Criar atalho"
3. Arraste o atalho para a área de trabalho
4. Dê duplo clique para iniciar

**Para ocultar a janela do terminal:**
- Use `Iniciar_Hub_Financeiro_Silencioso.vbs` em vez do .bat
- Crie atalho do arquivo .vbs

### Usando o Launcher Python
```powershell
# No terminal (dentro do venv):
python launcher.py
```

## Opção 2: Criar Executável Standalone

### Passo 1: Criar o .exe
```powershell
# Ativar ambiente virtual
.\venv\Scripts\Activate.ps1

# Rodar script de criação
python criar_executavel.py
```

### Passo 2: Copiar executável
```powershell
# Copiar de dist/ para raiz
copy dist\HubFinanceiro.exe .
```

### Passo 3: Criar atalho
1. Clique com botão direito em `HubFinanceiro.exe`
2. Selecione "Criar atalho"
3. Arraste para área de trabalho
4. (Opcional) Personalize ícone:
   - Botão direito no atalho → Propriedades
   - Alterar ícone → Escolha um .ico

## Opção 3: Atalho Manual do Streamlit

### Criar atalho do Streamlit direto
1. Clique com botão direito na área de trabalho
2. Novo → Atalho
3. Cole este caminho (ajuste o caminho para o seu usuário):
   ```
   C:\Users\lemop\Desktop\HUB-FINANCEIRO-STREAMLIT\venv\Scripts\python.exe -m streamlit run C:\Users\lemop\Desktop\HUB-FINANCEIRO-STREAMLIT\app.py
   ```
4. Nome: "Hub Financeiro"
5. Finalizar

### Configurar para abrir navegador automaticamente
1. Botão direito no atalho → Propriedades
2. Destino: adicionar parâmetros
   ```
   C:\Users\lemop\Desktop\HUB-FINANCEIRO-STREAMLIT\venv\Scripts\python.exe -m streamlit run C:\Users\lemop\Desktop\HUB-FINANCEIRO-STREAMLIT\app.py --server.headless true
   ```
3. Iniciar em: `C:\Users\lemop\Desktop\HUB-FINANCEIRO-STREAMLIT`

## Comparação das Opções

| Opção | Vantagens | Desvantagens |
|-------|-----------|--------------|
| **Batch (.bat)** | ✅ Simples, rápido, sem dependências<br>✅ Abre navegador automaticamente<br>✅ Mostra logs no console | ❌ Janela do terminal fica aberta |
| **VBS Script** | ✅ Não mostra janela<br>✅ Inicia em background<br>✅ Abre navegador automaticamente | ❌ Mais difícil debugar erros |
| **Launcher Python** | ✅ Abre navegador automaticamente<br>✅ Verifica dependências<br>✅ Mensagens de status | ❌ Requer ambiente virtual ativo |
| **Executável (.exe)** | ✅ Duplo clique direto<br>✅ Não precisa terminal<br>✅ Parece aplicativo nativo | ❌ Arquivo grande (~100MB)<br>❌ Precisa recriar a cada mudança |
| **Atalho Manual** | ✅ Leve<br>✅ Personalizável | ❌ Não abre navegador automaticamente<br>❌ Janela terminal fica aberta |

## Recomendação

**Para uso diário:** Use `Iniciar_Hub_Financeiro.bat` ou o `.vbs` (se quiser ocultar janela)
- Mais rápido
- Fácil de atualizar
- Abre navegador automaticamente

**Para distribuir:** Use o executável `.exe`
- Parece mais profissional
- Funciona sem Python instalado (com algumas limitações)
