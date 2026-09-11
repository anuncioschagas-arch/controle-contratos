#!/usr/bin/env python3
"""operador_id em contrato + get_contrato seguro (evita 500 se coluna nao existir)."""
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
        for marker in [
            'ALTER TABLE contrato ADD COLUMN quantidade_meses INTEGER DEFAULT 0")',
            'ALTER TABLE contrato ADD COLUMN quantidade_meses',
            'CREATE TABLE IF NOT EXISTS contrato',
        ]:
            p = t.find(marker)
            if p > 0:
                if "CREATE TABLE" in marker:
                    p2 = t.find('""")', p)
                    p = t.find("\n", p2) + 1
                else:
                    p = t.find("\n", p) + 1
                t = t[:p] + mig + t[p:]
                print("contrato operador migration")
                break

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

    new_get = '''
def get_contrato(id):
    with db_session() as conn:
        try:
            cols = [r[1] for r in conn.execute("PRAGMA table_info(contrato)").fetchall()]
            if "operador_id" not in cols:
                conn.execute("ALTER TABLE contrato ADD COLUMN operador_id INTEGER")
        except Exception:
            pass
        row = conn.execute("""
            SELECT c.*,
                   ct.nome AS contratante_nome, ct.documento AS contratante_doc,
                   ct.email AS contratante_email, ct.celular AS contratante_celular,
                   ct.logradouro AS contratante_logradouro, ct.numero AS contratante_numero,
                   ct.bairro AS contratante_bairro, ct.cidade AS contratante_cidade,
                   ct.uf AS contratante_uf, ct.cep AS contratante_cep,
                   cd.nome AS contratado_nome, cd.documento AS contratado_doc,
                   cd.email AS contratado_email, cd.celular AS contratado_celular,
                   cd.logradouro AS contratado_logradouro, cd.numero AS contratado_numero,
                   cd.bairro AS contratado_bairro, cd.cidade AS contratado_cidade,
                   cd.uf AS contratado_uf, cd.cep AS contratado_cep,
                   cd.foto_documento AS contratado_foto_documento,
                   cd.foto_comprovante AS contratado_foto_comprovante,
                   s.nome AS setor_nome, s.responsavel AS setor_responsavel,
                   op.nome AS operador_nome
            FROM contrato c
            LEFT JOIN contratante ct ON c.contratante_id = ct.id
            LEFT JOIN contratado cd ON c.contratado_id = cd.id
            LEFT JOIN setor s ON c.setor_id = s.id
            LEFT JOIN usuario op ON c.operador_id = op.id
            WHERE c.id = ?
        """, (id,)).fetchone()
        return dict(row) if row else None
'''
    start = t.find("def get_contrato(")
    if start >= 0:
        rest = t[start + 4 :]
        m = re.search(r"\ndef ", rest)
        end = start + 4 + m.start() if m else len(t)
        t = t[:start] + new_get.strip() + "\n\n" + t[end + 1 :]
        print("get_contrato safe replaced")

    if "operador_id=?" not in t[t.find("def save_contrato"): t.find("def save_contrato") + 600]:
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
        print("save_contrato fields attempted")

    if "def save_contrato" in t and "PRAGMA table_info(contrato)" not in t[t.find("def save_contrato"): t.find("def save_contrato") + 350]:
        t = t.replace(
            "data = aplicar_calculos_contrato(data)\n\n    with db_session() as conn:\n        if id:",
            "data = aplicar_calculos_contrato(data)\n\n    with db_session() as conn:\n"
            "        try:\n"
            "            cols = [r[1] for r in conn.execute(\"PRAGMA table_info(contrato)\").fetchall()]\n"
            "            if \"operador_id\" not in cols:\n"
            "                conn.execute(\"ALTER TABLE contrato ADD COLUMN operador_id INTEGER\")\n"
            "        except Exception:\n"
            "            pass\n"
            "        if id:",
            1,
        )
        print("save pragma")

    dbp.write_text(t, encoding="utf-8")

try:
    import sqlite3
    for name in ("contratos.db", "data/contratos.db"):
        p = Path(name)
        if p.exists():
            conn = sqlite3.connect(str(p))
            cols = [r[1] for r in conn.execute("PRAGMA table_info(contrato)").fetchall()]
            if "operador_id" not in cols:
                conn.execute("ALTER TABLE contrato ADD COLUMN operador_id INTEGER")
                conn.commit()
                print("DB migrated", name)
            conn.close()
except Exception as e:
    print("db migrate skip", e)

form = Path("templates/form_contrato.html")
if form.exists() and "campo-operador-contrato" not in form.read_text(encoding="utf-8"):
    f = form.read_text(encoding="utf-8")
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
        f = f.replace("<label>Valor Total (R$) *</label>", block + "\n                <label>Valor Total (R$) *</label>", 1)
        form.write_text(f, encoding="utf-8")
        print("form operador")

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
            t = t[:start] + t[start:end].replace("setores=setores,", "setores=setores, operadores=operadores,") + t[end:]
        start = t.find("def editar_contrato")
        if start > 0:
            m = re.search(r"\ndef ", t[start + 4 :])
            end = start + 4 + m.start() if m else len(t)
            t = t[:start] + t[start:end].replace("setores=setores,", "setores=setores, operadores=operadores,") + t[end:]
        print("app render")
    app.write_text(t, encoding="utf-8")

print("fix_contrato_operador done")
