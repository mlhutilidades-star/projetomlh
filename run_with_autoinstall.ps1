# ========================================
#  MLH - Modo Autônomo Completo
# ========================================
# Inicia todos os monitores e o Aider em modo automático

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host " 🔄 MLH - Modo Autônomo Completo" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Define o diretório do script como diretório de trabalho
$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $scriptPath

# Verifica se o venv existe
if (-not (Test-Path ".venv-aider\Scripts\Activate.ps1")) {
    Write-Host "[ERRO] Ambiente virtual .venv-aider não encontrado!" -ForegroundColor Red
    Write-Host "Execute primeiro: python -m venv .venv-aider" -ForegroundColor Yellow
    Read-Host "Pressione Enter para sair"
    exit 1
}

Write-Host "[1/4] Ativando ambiente virtual .venv-aider..." -ForegroundColor Green
& ".venv-aider\Scripts\Activate.ps1"

Write-Host "[2/4] Iniciando monitor de requirements.txt em segundo plano..." -ForegroundColor Green
Start-Process powershell -ArgumentList "-NoExit", "-Command", "& '.venv-aider\Scripts\Activate.ps1'; python monitor_requirements.py" -WindowStyle Normal

Write-Host "[3/4] Iniciando monitor de agente autônomo em segundo plano..." -ForegroundColor Green
Start-Process powershell -ArgumentList "-NoExit", "-Command", "& '.venv-aider\Scripts\Activate.ps1'; python monitor_agent.py" -WindowStyle Normal

Write-Host "[4/4] Aguardando 3 segundos antes de iniciar Aider principal..." -ForegroundColor Green
Start-Sleep -Seconds 3

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host " ✅ Modo Autônomo MLH INICIADO" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Módulos ativos:" -ForegroundColor Yellow
Write-Host "  📦 Monitor de dependências (requirements.txt)" -ForegroundColor White
Write-Host "  🤖 Monitor de tarefas (TODO/STATUS)" -ForegroundColor White
Write-Host "  🚀 Aider em modo automático" -ForegroundColor White
Write-Host ""
Write-Host "Configuração Aider:" -ForegroundColor Yellow
Write-Host "  - Model: gpt-4o" -ForegroundColor White
Write-Host "  - Auto-commits: habilitado" -ForegroundColor White
Write-Host "  - Watch-files: habilitado" -ForegroundColor White
Write-Host "  - Auto-yes: habilitado" -ForegroundColor White
Write-Host ""
Write-Host "⚠️  Todos os monitores estão sendo executados" -ForegroundColor Yellow
Write-Host "    em janelas separadas. Feche-as manualmente" -ForegroundColor Yellow
Write-Host "    quando encerrar o trabalho." -ForegroundColor Yellow
Write-Host ""
Write-Host "Pressione Ctrl+C para encerrar APENAS o Aider principal" -ForegroundColor Yellow
Write-Host ""

# Inicia Aider com configurações automáticas
aider --model gpt-4o --yes --auto-commits --watch-files .

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host " Aider principal encerrado" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "⚠️  ATENÇÃO: Os monitores ainda estão rodando!" -ForegroundColor Yellow
Write-Host "    Feche as janelas:" -ForegroundColor Yellow
Write-Host "      - Monitor Requirements" -ForegroundColor White
Write-Host "      - Monitor Agent" -ForegroundColor White
Write-Host ""
Read-Host "Pressione Enter para sair"

