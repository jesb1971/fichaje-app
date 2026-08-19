@echo off
title Sistema de Fichaje ICADEPRO
cd /d "%~dp0"

call venv\Scripts\activate.bat

echo.
echo ========================================
echo   SISTEMA DE FICHAJE ICADEPRO
echo ========================================
echo.
echo Iniciando aplicacion...
echo.

python -m uvicorn main:app --reload

pause