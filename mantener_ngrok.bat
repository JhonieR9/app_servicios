@echo off
title Ngrok TalentHub 24/7
color 0B
echo ========================================
echo    NGROK TALENTHUB - MODO 24/7
echo ========================================
echo.
echo [%time%] Iniciando ngrok...
echo.
echo Espera a que aparezca la URL publica...
echo.
echo IMPORTANTE: NO CIERRES ESTA VENTANA
echo.

ngrok http 8000

echo.
echo [%time%] Ngrok detenido
pause
