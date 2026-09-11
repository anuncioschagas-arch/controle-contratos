#!/usr/bin/env python3
"""Adiciona operador_id ao contrato e campo no formulario."""
from pathlib import Path
import re

dbp = Path("database.py")
if dbp.exists():
    t = dbp.read_text(encoding="utf-8")
    if 'contrato", "operador_id"' not in t:
        mig = '''
        if not _coluna_existe(cur, "contrato", "operador_id"):
            cur.execute("ALTER TABLE contrato ADD COLUMN operador_id INTEGER")
'''
        if "quantidade_meses" in t:
            p = t.find("ALTER TABLE contrato ADD COLUMN quantidade_meses")
            if p > 0:
                p = t.find("\n", p) + 1
                t = t[:p] + mig + t[p:]
                print("contrato operador migration")
            else:
                p = t.find("CREATE TABLE IF NOT EXISTS contrato")
                if p > 0:
                    p2 = t.find('""")', p)
                    p2 = t.find("\n", p2) + 1
                    t = t[:p2] + mig + t[p2:]
                    print("contrato operador migration after create")
    if "def list_operadores" not in t:
        t += '''

def list_operadores():
    with db_session() as conn:
        rows = conn.execute(
            "SELECT id, nome, login, perfil FROM usuario WHERE ativo = 1 AND perfil IN ('operador', 'admin') ORDER BY nome"
        ).fetchall()
        return [dict(r) for r in rows]
'''
        print("list_operadores")
    if "operador_id=?" not in t[t.find("def save_contrato"): t.find("def save_contrato") + 500]:
        t = t.replace(
            "numero=?, contratante_id=?, contratado_id=?, setor_id=?,\n                    objeto=?",
            "numero=?, contratante_id=?, contratado_id=?, setor_id=?, operador_id=?,\n                    objeto=?",
        )
        t = t.replace(
            'data.get("setor_id") or None, data["objeto"]',
            'data.get("setor_id") or None, data.get("operador_id") or None, data["objeto"]',
            2,
        )
        t = t.replace(
            "(numero, contratante_id, contratado_id, setor_id, objeto, valor,",
            "(numero, contratante_id, contratado_id, setor_id, operador_id, objeto, valor,",
        )
        t = t.replace(
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            1,
        )
        print("save_contrato operador")
    if "operador_nome" not in t[t.find("def get_contrato"): t.find("def get_contrato") + 800]:
        t = t.replace(
            "s.nome AS setor_nome, s.responsavel AS setor_responsavel\n            FROM contrato c",
            "s.nome AS setor_nome, s.responsavel AS setor_responsavel,\n                   op.nome AS operador_nome\n            FROM contrato c",
        )
        t = t.replace(
            "LEFT JOIN setor s ON c.setor_id = s.id\n            WHERE c.id = ?",
            "LEFT JOIN setor s ON c.setor_id = s.id\n            LEFT JOIN usuario op ON c.operador_id = op.id\n            WHERE c.id = ?",
        )
        print("get_contrato operador")
    dbp.write_text(t, encoding="utf-8")

form = Path("templates/form_contrato.html")
if form.exists():
    f = form.read_text(encoding="utf-8")
    if "campo-operador-contrato" not in f:
        block = '''
            <div class="form-group">
                <label>Operador responsável</label>
                <select name="operador_id" id="campo-operador-contrato">
                    <option value="">— Selecione o operador —</option>
                    {% for op in operadores or [] %}
                    <option value="{{ op.id }}"
                        {% if item and item.operador_id and item.operador_id|int == op.id|int %}selected{% endif %}>
                        #{{ op.id }} — {{ op.nome }} ({{ op.perfil }})
                    </option>
                    {% endfor %}
                </select>
            </div>
'''
        if "<label>Valor Total (R$) *</label>" in f:
            f = f.replace(
                "<label>Valor Total (R$) *</label>",
                block + "\n                <label>Valor Total (R$) *</label>",
                1,
            )
            form.write_text(f, encoding="utf-8")
            print("form operador")
    else:
        print("form ok")

app = Path("app.py")
if app.exists():
    t = app.read_text(encoding="utf-8")
    old = '''        data = form_to_dict([
            "numero", "contratante_id", "contratado_id", "setor_id",
            "objeto", "valor", "data_inicio", "data_fim", "status", "observacoes",
        ])
        data["contratante_id"] = int(data["contratante_id"]) if data.get("contratante_id") else None
        data["contratado_id"] = int(data["contratado_id"]) if data.get("contratado_id") else None
        data["setor_id"] = int(data["setor_id"]) if data.get("setor_id") else None
'''
    new = '''        data = form_to_dict([
            "numero", "contratante_id", "contratado_id", "setor_id", "operador_id",
            "objeto", "valor", "data_inicio", "data_fim", "status", "observacoes",
        ])
        data["contratante_id"] = int(data["contratante_id"]) if data.get("contratante_id") else None
        data["contratado_id"] = int(data["contratado_id"]) if data.get("contratado_id") else None
        data["setor_id"] = int(data["setor_id"]) if data.get("setor_id") else None
        data["operador_id"] = int(data["operador_id"]) if data.get("operador_id") else None
'''
    if old in t:
        t = t.replace(old, new)
        print("app fields")
    if "operadores = db.list_operadores" not in t:
        t = t.replace(
            "contratantes, contratados, setores = _listas_para_contrato()",
            "contratantes, contratados, setores = _listas_para_contrato()\n    operadores = db.list_operadores() if hasattr(db, \"list_operadores\") else []",
        )
        print("app operadores var")
    if "operadores=operadores" not in t[t.find("def novo_contrato"): t.find("def novo_contrato") + 1500]:
        start = t.find("def novo_contrato")
        end = t.find("def editar_contrato")
        if start > 0 and end > start:
            chunk = t[start:end].replace("setores=setores,", "setores=setores, operadores=operadores,")
            t = t[:start] + chunk + t[end:]
        start = t.find("def editar_contrato")
        if start > 0:
            m = re.search(r"\ndef ", t[start + 4 :])
            end = start + 4 + m.start() if m else len(t)
            chunk = t[start:end].replace("setores=setores,", "setores=setores, operadores=operadores,")
            t = t[:start] + chunk + t[end:]
        print("app render operadores")
    app.write_text(t, encoding="utf-8")
print("fix_contrato_operador done")
