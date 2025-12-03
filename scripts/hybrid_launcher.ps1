# ========================================
#  MLH - Hybrid Launcher (Aider + Copilot)
# ========================================
# Orquestra todo o sistema autonomo

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host " MLH - Sistema Hibrido Iniciando" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Define o diretorio do script como diretorio de trabalho
$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
$rootPath = Split-Path -Parent $scriptPath
Set-Location $rootPath

# Verifica se o venv existe
if (-not (Test-Path ".venv-aider\Scripts\Activate.ps1")) {
    Write-Host "[ERRO] Ambiente virtual .venv-aider nao encontrado!" -ForegroundColor Red
    Write-Host "Execute primeiro: python -m venv .venv-aider" -ForegroundColor Yellow
    Read-Host "Pressione Enter para sair"
    exit 1
}

Write-Host "[1/5] Verificando ambiente virtual..." -ForegroundColor Green
& ".venv-aider\Scripts\Activate.ps1"
Write-Host "      OK Ambiente .venv-aider ativado" -ForegroundColor Gray

Write-Host "[2/5] Iniciando Auto-Installer (monitor de dependencias)..." -ForegroundColor Green
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$rootPath'; & '.venv-aider\Scripts\Activate.ps1'; python monitor_requirements.py" -WindowStyle Minimized
Start-Sleep -Milliseconds 500
Write-Host "      OK Auto-Installer rodando em segundo plano" -ForegroundColor Gray

Write-Host "[3/5] Iniciando Auto-Agent Monitor (monitor de tarefas)..." -ForegroundColor Green
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$rootPath'; & '.venv-aider\Scripts\Activate.ps1'; python monitor_agent.py" -WindowStyle Minimized
Start-Sleep -Milliseconds 500
Write-Host "      OK Auto-Agent Monitor rodando em segundo plano" -ForegroundColor Gray

Write-Host "[4/5] Aguardando 3 segundos antes de iniciar Aider..." -ForegroundColor Green
Start-Sleep -Seconds 3

Write-Host "[5/5] Verificando instalacao do Aider..." -ForegroundColor Green
try {
    $aiderVersion = & aider --version 2>&1
    Write-Host "      OK Aider detectado: $aiderVersion" -ForegroundColor Gray
} catch {
    Write-Host "      Aider nao encontrado, instalando..." -ForegroundColor Yellow
    python -m pip install aider-chat
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host " ✅ SISTEMA HÍBRIDO OPERACIONAL" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "Componentes Ativos:" -ForegroundColor Yellow
Write-Host "  📦 Auto-Installer" -ForegroundColor White -NoNewline
Write-Host "      (minimizado)" -ForegroundColor Gray
Write-Host "  🤖 Auto-Agent Monitor" -ForegroundColor White -NoNewline
Write-Host " (minimizado)" -ForegroundColor Gray
Write-Host "  🚀 Aider GPT-4" -ForegroundColor White -NoNewline
Write-Host "        (iniciando...)" -ForegroundColor Gray
Write-Host ""

Write-Host "Configuração Aider:" -ForegroundColor Yellow
Write-Host "  - Model: gpt-4o" -ForegroundColor White
Write-Host "  - Auto-commits: ✓" -ForegroundColor White
Write-Host "  - Watch-files: ✓" -ForegroundColor White
Write-Host "  - Auto-yes: ✓" -ForegroundColor White
Write-Host ""

Write-Host "Logs disponíveis em:" -ForegroundColor Yellow
Write-Host "  - logs\auto_installer.log" -ForegroundColor White
Write-Host "  - logs\auto_agent.log" -ForegroundColor White
Write-Host "  - logs\copilot_supervisor.log" -ForegroundColor White
Write-Host ""

Write-Host "Documentação:" -ForegroundColor Yellow
Write-Host "  - ..\PROJETO MLH\docs\HYBRID_README.md" -ForegroundColor White
Write-Host "  - ..\PROJETO MLH\docs\MLH_SUPERVISOR.md" -ForegroundColor White
Write-Host "  - ..\PROJETO MLH\docs\MLH_TURBO_RULES.md" -ForegroundColor White
Write-Host ""

Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
Write-Host "  SUPERVISÃO COPILOT: ATIVADA" -ForegroundColor Green
Write-Host "  Modo: TURBO" -ForegroundColor Yellow
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
Write-Host ""

Write-Host "Aguarde, Aider está iniciando..." -ForegroundColor Cyan
Write-Host "Pressione Ctrl+C para encerrar o Aider principal" -ForegroundColor Yellow
Write-Host "(Monitores continuarão rodando em segundo plano)" -ForegroundColor Gray
Write-Host ""

# Inicia Aider no terminal principal
& aider --model gpt-4o --yes --auto-commits --watch-files .

# Após Aider encerrar
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host " Aider Encerrado" -ForegroundColor Yellow
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "⚠️  ATENÇÃO: Os monitores ainda estão rodando!" -ForegroundColor Yellow
Write-Host ""
Write-Host "Para encerrar tudo:" -ForegroundColor White
Write-Host "  1. Feche as janelas minimizadas do PowerShell" -ForegroundColor Gray
Write-Host "  2. Ou execute: Stop-Process -Name powershell -Force" -ForegroundColor Gray
Write-Host ""

Read-Host "Pressione Enter para sair"
