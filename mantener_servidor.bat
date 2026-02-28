@echo off
title Servidor TalentHub 24/7
color 0A
echo ========================================
echo   SERVIDOR TALENTHUB - MODO 24/7
echo ========================================
echo.
echo [%time%] Iniciando servidor...
echo.
echo URL Local: http://localhost:8000
echo Formulario: http://localhost:8000/trabajador/registro
echo Panel Admin: http://localhost:8000/trabajador/admin/login
echo.
echo IMPORTANTE: NO CIERRES ESTA VENTANA
echo.

cd /d "%~dp0"
uvicorn main:app --host 0.0.0.0 --port 8000

echo.
echo [%time%] Servidor detenido
pause
