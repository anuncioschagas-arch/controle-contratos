#!/bin/bash
cd "$(dirname "$0")"
echo ""
echo "========================================"
echo "  Controle de Contratos"
echo "========================================"
echo ""
echo "Verificando dependencias..."
if ! python3 -c "import jinja2" 2>/dev/null; then
    echo ""
    echo "Instalando jinja2 e reportlab..."
    pip3 install jinja2 reportlab || pip install jinja2 reportlab
    echo ""
fi
echo ""
echo "Iniciando o sistema..."
echo ""
python3 app.py
