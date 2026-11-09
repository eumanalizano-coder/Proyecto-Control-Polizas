@echo off
rem iniciar_app.bat
rem Enciende la aplicacion Flask con uv. Cerrar esta ventana apaga el servidor.
chcp 65001 >nul
cd /d "%~dp0"

rem uv se instala en esta carpeta; la agregamos al PATH por si no esta.
set "PATH=%USERPROFILE%\.local\bin;%PATH%"

echo Iniciando Control de Polizas en http://127.0.0.1:5000 ...
uv run app.py

echo.
echo La aplicacion se detuvo.
pause
