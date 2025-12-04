@echo off
REM ========================================
REM  MLH - Modo Autônomo Completo
REM ========================================
REM Inicia todos os monitores e o Aider em modo automático

echo.
echo ========================================
echo  🔄 MLH - Modo Autônomo Completo
echo ========================================
echo.

REM Define o diretório do script como diretório de trabalho
cd /d "%~dp0"

REM Verifica se o venv existe
if not exist ".venv-aider\Scripts\activate.bat" (
    echo [ERRO] Ambiente virtual .venv-aider não encontrado!
    echo Execute primeiro: python -m venv .venv-aider
    pause
    exit /b 1
)

echo [1/4] Ativando ambiente virtual .venv-aider...
call .venv-aider\Scripts\activate.bat

echo [2/4] Iniciando monitor de requirements.txt em segundo plano...
start "📦 Monitor Requirements" cmd /k "call .venv-aider\Scripts\activate.bat && python monitor_requirements.py"

echo [3/4] Iniciando monitor de agente autônomo em segundo plano...
start "🤖 Monitor Agent" cmd /k "call .venv-aider\Scripts\activate.bat && python monitor_agent.py"

echo [4/4] Aguardando 3 segundos antes de iniciar Aider principal...
timeout /t 3 /nobreak >nul

echo.
echo ========================================
echo  ✅ Modo Autônomo MLH INICIADO
echo ========================================
echo.
echo Módulos ativos:
echo   📦 Monitor de dependências (requirements.txt)
echo   🤖 Monitor de tarefas (TODO/STATUS)
echo   🚀 Aider em modo automático
echo.
echo Configuração Aider:
echo   - Model: gpt-4o
echo   - Auto-commits: habilitado
echo   - Watch-files: habilitado
echo   - Auto-yes: habilitado
echo.
echo ⚠️  Todos os monitores estão sendo executados
echo     em janelas separadas. Feche-as manualmente
echo     quando encerrar o trabalho.
echo.
echo Pressione Ctrl+C para encerrar APENAS o Aider principal
echo.

REM Inicia Aider com configurações automáticas
aider --model gpt-4o --yes --auto-commits --watch-files .

echo.
echo ========================================
echo  Aider principal encerrado
echo ========================================
echo.
echo ⚠️  ATENÇÃO: Os monitores ainda estão rodando!
echo     Feche as janelas:
echo       - "Monitor Requirements"
echo       - "Monitor Agent"
echo.
pause

