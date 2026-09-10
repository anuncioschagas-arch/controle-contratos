@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo.
echo ========================================
echo   Controle de Contratos
echo ========================================
echo.
echo Verificando dependencias...
python -c "import jinja2" 2>nul
if errorlevel 1 (
    echo.
    echo Instalando jinja2 e reportlab...
    pip install jinja2 reportlab
    echo.
)
echo.
echo Iniciando o sistema...
echo.
python app.py
pause
