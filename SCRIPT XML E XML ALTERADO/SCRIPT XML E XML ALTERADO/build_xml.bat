@echo off
chcp 65001 > nul
setlocal enabledelayedexpansion

echo.
echo ========================================
echo   COMPILADOR - GERADOR DE NFe UNIVERSAL
echo ========================================
echo.

echo Verificando Python...
python --version > nul 2>&1
if %errorlevel% neq 0 (
    echo.
    echo ERRO: Python nao encontrado!
    echo.
    echo Baixe Python em: https://www.python.org/downloads/
    echo IMPORTANTE: Marque "Add Python to PATH" durante a instalacao
    echo.
    pause
    exit /b 1
)

echo Python encontrado. OK
echo.

echo Instalando PyInstaller...
python -m pip install --upgrade pip --quiet 2>nul
python -m pip install pyinstaller --quiet 2>nul
python -m pip install pdfplumber --quiet 2>nul

echo Dependencias instaladas. OK
echo.

echo Compilando app_universal.exe (pode levar alguns minutos)...
pyinstaller --onefile --console --distpath . app_universal.py

echo.
if exist app_universal.exe (
    echo ========================================
    echo SUCESSO! app_universal.exe foi gerado!
    echo ========================================
    echo.
    echo O arquivo executavel esta pronto: app_universal.exe
    echo.
) else (
    echo.
    echo ERRO na compilacao!
    echo Tente novamente ou verifique se app_universal.py existe.
    echo.
)

echo.
pause