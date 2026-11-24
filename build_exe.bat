@echo off
chcp 65001 > nul
title Avito SDK Pro — Standalone Build
echo ========================================================
echo   Сборка автономного дистрибутива Avito SDK Pro...
echo ========================================================
cd /d "%~dp0"

where uv >nul 2>nul
if %ERRORLEVEL% equ 0 (
    uv run --no-sync pyinstaller AvitoSDK_Pro.spec --noconfirm
) else (
    pyinstaller AvitoSDK_Pro.spec --noconfirm
)

if %ERRORLEVEL% equ 0 (
    echo.
    echo [OK] Сборка успешно завершена в dist\AvitoSDK_Pro!
    echo Создание zip архива...
    powershell -Command "Compress-Archive -Path 'dist\AvitoSDK_Pro\*' -DestinationPath 'dist\AvitoSDK_Pro_Windows_x64.zip' -Force"
    echo Готово: dist\AvitoSDK_Pro_Windows_x64.zip
) else (
    echo.
    echo [ERROR] Сборка завершилась с ошибкой.
)
pause
