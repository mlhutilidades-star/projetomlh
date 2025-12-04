@echo off
chcp 65001 > nul
setlocal enabledelayedexpansion

if exist app_universal.exe (
    app_universal.exe
) else (
    echo.
    echo ERRO: app_universal.exe nao encontrado!
    echo.
    echo Execute primeiro o arquivo build.bat para compilar.
    echo.
    pause
)