@echo off
title Hub Financeiro - Iniciando...
cd /d "%~dp0"

echo ========================================
echo    HUB FINANCEIRO - STREAMLIT
echo ========================================
echo.

REM Verificar se venv existe
if not exist "venv\Scripts\python.exe" (
    echo [ERRO] Ambiente virtual nao encontrado!
    echo.
    echo Por favor, crie o ambiente virtual primeiro:
    echo    python -m venv venv
    echo    .\venv\Scripts\Activate.ps1
    echo    pip install -r requirements.txt
    echo.
    pause
    exit /b 1
)

echo [OK] Ambiente virtual encontrado
echo [*] Ativando ambiente...

REM Ativar venv e iniciar Streamlit
call venv\Scripts\activate.bat

echo [*] Iniciando servidor Streamlit...
echo.
echo ========================================
echo   SERVIDOR RODANDO
echo ========================================
echo.
echo Acesse: http://localhost:8501
echo.
echo ATENCAO: NAO FECHE ESTA JANELA!
echo          O sistema esta rodando aqui.
echo.
echo Para encerrar: pressione Ctrl+C
echo.
echo ========================================
echo.

REM Abrir navegador após 3 segundos
start "" timeout /t 3 /nobreak ^>nul ^& start http://localhost:8501

REM Iniciar Streamlit
streamlit run app.py

echo.
echo [*] Servidor encerrado.
pause
