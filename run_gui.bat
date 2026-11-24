@echo off
chcp 65001 > nul
title Avito SDK Pro — Desktop Launcher
echo ========================================================
echo   Запуск Avito SDK Pro (Графический интерфейс)...
echo ========================================================
cd /d "%~dp0"

where uv >nul 2>nul
if %ERRORLEVEL% equ 0 (
    uv run --no-sync python run_gui.py
) else (
    python run_gui.py
)

if %ERRORLEVEL% neq 0 (
    echo.
    echo Ошибка при запуске. Убедитесь, что установлен Python и зависимости:
    echo uv pip install customtkinter curl-cffi
    echo.
    pause
)
