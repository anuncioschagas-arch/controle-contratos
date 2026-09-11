#!/bin/bash
set -e
if [ -f ensure_static.py ]; then python ensure_static.py || true; fi
if [ -f fix_ui.py ]; then python fix_ui.py || true; fi
if [ -f fix_login.py ]; then python fix_login.py || true; fi
if [ -f apply_updates.py ]; then python apply_updates.py || true; fi
if [ -f runtime_patch.py ]; then python runtime_patch.py || true; fi
if [ -f chat_install.py ]; then python chat_install.py || true; fi
if [ -f fix_contratante_form.py ]; then python fix_contratante_form.py || true; fi
if [ -f fix_doc_edit.py ]; then python fix_doc_edit.py || true; fi
if [ -f fix_contrato_operador.py ]; then python fix_contrato_operador.py || true; fi
if [ -f fix_ver_contrato.py ]; then python fix_ver_contrato.py || true; fi
if [ -f fix_editar_contrato.py ]; then python fix_editar_contrato.py || true; fi
if [ -f fix_consultas_filtros.py ]; then python fix_consultas_filtros.py || true; fi
exec python app.py
