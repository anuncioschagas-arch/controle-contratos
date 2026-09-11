#!/usr/bin/env python3
"""Patches no boot: SQL contratados + bloqueio CPF/CNPJ duplicado (forçado no app.py)."""
from pathlib import Path
import re

FIXED_LIST = '''
def list_contratados(search=None, contratante_id=None):
    """Lista contratados com nome do contratante."""
    with db_session() as conn:
        where = []
        params = []
        if contratante_id:
            cid = int(contratante_id)
            where.append(
                "(cd.contratante_id = ? OR cd.id IN ("
                "SELECT c.contratado_id FROM contrato c "
                "WHERE c.contratante_id = ? AND c.contratado_id IS NOT NULL"
                "))"
            )
            params.extend([cid, cid])
        if search:
            where.append("(cd.nome LIKE ? OR cd.documento LIKE ?)")
            params.extend(["%%%s%%" % search, "%%%s%%" % search])
        sql = (
            "SELECT cd.*, ct.nome AS contratante_nome "
            "FROM contratado cd "
            "LEFT JOIN contratante ct ON cd.contratante_id = ct.id"
        )
        if where:
            sql += " WHERE " + " AND ".join(where)
        sql += " ORDER BY cd.nome"
        rows = conn.execute(sql, params).fetchall()
        return [dict(r) for r in rows]
'''

DOC_DB = '''
def normalizar_documento(doc):
    if not doc:
        return ""
    return re.sub(r"\\D", "", str(doc))

class DocumentoDuplicado(Exception):
    pass

def documento_ja_existe(documento, excluir_contratante_id=None, excluir_contratado_id=None):
    digits = normalizar_documento(documento)
    if not digits or len(digits) < 11:
        return None
    with db_session() as conn:
        for r in conn.execute("SELECT id, nome, documento FROM contratante").fetchall():
            if excluir_contratante_id and int(r["id"]) == int(excluir_contratante_id):
                continue
            if normalizar_documento(r["documento"]) == digits:
                return {"tabela": "contratante", "id": r["id"], "nome": r["nome"]}
        for r in conn.execute("SELECT id, nome, documento FROM contratado").fetchall():
            if excluir_contratado_id and int(r["id"]) == int(excluir_contratado_id):
                continue
            if normalizar_documento(r["documento"]) == digits:
                return {"tabela": "contratado", "id": r["id"], "nome": r["nome"]}
    return None
'''

dbp = Path("database.py")
if dbp.exists():
    t = dbp.read_text(encoding="utf-8")
    if "import re" not in t.split("def ")[0]:
        t = t.replace("import os", "import os\nimport re", 1) if "import os" in t else "import re\n" + t
    if "def documento_ja_existe" not in t:
        t = t.replace("def save_contratante(data, id=None):", DOC_DB + "\ndef save_contratante(data, id=None):", 1)
    if "documento_ja_existe(doc" not in t[t.find("def save_contratante"):t.find("def save_contratante")+400]:
        t = t.replace(
            "def save_contratante(data, id=None):\n    with db_session() as conn:\n        if id:",
            "def save_contratante(data, id=None):\n"
            "    doc = data.get(\"documento\")\n"
            "    if doc:\n"
            "        dup = documento_ja_existe(doc, excluir_contratante_id=id)\n"
            "        if dup:\n"
            "            raise DocumentoDuplicado(\"CPF/CNPJ já cadastrado em %s #%s — %s. Não é permitido duplicar.\" % (dup[\"tabela\"], dup[\"id\"], dup[\"nome\"]))\n"
            "    with db_session() as conn:\n"
            "        if id:",
            1,
        )
    if "def save_contratado" in t and "documento_ja_existe(doc" not in t[t.find("def save_contratado"):t.find("def save_contratado")+400]:
        t = re.sub(
            r"def save_contratado\(data, id=None\):\n    with db_session\(\) as conn:\n        if id:",
            "def save_contratado(data, id=None):\n"
            "    doc = data.get(\"documento\")\n"
            "    if doc:\n"
            "        dup = documento_ja_existe(doc, excluir_contratado_id=id)\n"
            "        if dup:\n"
            "            raise DocumentoDuplicado(\"CPF/CNPJ já cadastrado em %s #%s — %s. Não é permitido duplicar.\" % (dup[\"tabela\"], dup[\"id\"], dup[\"nome\"]))\n"
            "    with db_session() as conn:\n"
            "        if id:",
            t, count=1,
        )
    m = re.search(r"^def list_contratados\(.*?(?=^def )", t, re.M | re.S)
    if m:
        t = t[:m.start()] + FIXED_LIST.strip() + "\n\n" + t[m.end():]
    dbp.write_text(t, encoding="utf-8")
    print("database.py patched")

APP_HELPER = r'''
def _so_digitos_doc(doc):
    return re.sub(r"\D", "", str(doc or ""))

def verificar_documento_unico(documento, excluir_contratante_id=None, excluir_contratado_id=None):
    digits = _so_digitos_doc(documento)
    if not digits or len(digits) < 11:
        return None
    for ct in db.list_contratantes():
        if excluir_contratante_id and int(ct["id"]) == int(excluir_contratante_id):
            continue
        if _so_digitos_doc(ct.get("documento")) == digits:
            return "CPF/CNPJ já cadastrado no CONTRATANTE #%s — %s. Não é permitido duplicar." % (ct["id"], ct.get("nome") or "")
    try:
        import sqlite3 as _sq
        from database import DB_PATH as _DBP
        _conn = _sq.connect(_DBP)
        _conn.row_factory = _sq.Row
        for cd in _conn.execute("SELECT id, nome, documento FROM contratado").fetchall():
            if excluir_contratado_id and int(cd["id"]) == int(excluir_contratado_id):
                continue
            if _so_digitos_doc(cd["documento"]) == digits:
                _conn.close()
                return "CPF/CNPJ já cadastrado no CONTRATADO #%s — %s. Não é permitido duplicar." % (cd["id"], cd["nome"] or "")
        _conn.close()
    except Exception:
        for cd in db.list_contratados():
            if excluir_contratado_id and int(cd["id"]) == int(excluir_contratado_id):
                continue
            if _so_digitos_doc(cd.get("documento")) == digits:
                return "CPF/CNPJ já cadastrado no CONTRATADO #%s — %s. Não é permitido duplicar." % (cd["id"], cd.get("nome") or "")
    return None

'''

app = Path("app.py")
if app.exists():
    t = app.read_text(encoding="utf-8")
    if "import re" not in t.split("def ")[0] and "import re\n" not in t[:500]:
        t = t.replace("import os", "import os\nimport re", 1) if "import os" in t else "import re\n" + t
    if "def verificar_documento_unico" not in t:
        idx = t.find("@app.route")
        if idx > 0:
            t = t[:idx] + APP_HELPER + "\n" + t[idx:]
            print("app helper inserted")

    def inject_before(src, needle, check_code):
        out = []
        i = 0
        while True:
            j = src.find(needle, i)
            if j < 0:
                out.append(src[i:])
                break
            window = src[max(0, j-200):j]
            if "verificar_documento_unico" in window:
                out.append(src[i:j+len(needle)])
                i = j + len(needle)
                continue
            out.append(src[i:j])
            out.append(check_code + needle)
            i = j + len(needle)
        return "".join(out)

    t2 = inject_before(
        t,
        'db.save_contratante(data)\n',
        'erro_doc = verificar_documento_unico(data.get("documento"))\n'
        '        if erro_doc:\n'
        '            return render("form_pessoa.html", titulo="Novo Contratante", item=data,\n'
        '                base_url="/contratantes", action="/contratantes/novo",\n'
        '                message=erro_doc, message_type="error")\n'
        '        ',
    )
    t2 = inject_before(
        t2,
        'db.save_contratante(data, id=id)\n',
        'erro_doc = verificar_documento_unico(data.get("documento"), excluir_contratante_id=id)\n'
        '        if erro_doc:\n'
        '            return render("form_pessoa.html", titulo="Editar Contratante", item=data,\n'
        '                base_url="/contratantes", action="/contratantes/%d/editar" % id,\n'
        '                message=erro_doc, message_type="error")\n'
        '        ',
    )
    t2 = inject_before(
        t2,
        'db.save_contratado(data)\n',
        'erro_doc = verificar_documento_unico(data.get("documento"))\n'
        '        if erro_doc:\n'
        '            return render("form_pessoa.html", titulo="Novo Contratado", item=data,\n'
        '                base_url="/contratados", action="/contratados/novo", com_fotos=True,\n'
        '                mostrar_contratante=True, contratantes=db.list_contratantes(),\n'
        '                message=erro_doc, message_type="error")\n'
        '        ',
    )
    t2 = inject_before(
        t2,
        'db.save_contratado(data, id=id)\n',
        'erro_doc = verificar_documento_unico(data.get("documento"), excluir_contratado_id=id)\n'
        '        if erro_doc:\n'
        '            return render("form_pessoa.html", titulo="Editar Contratado", item=data,\n'
        '                base_url="/contratados", action="/contratados/%d/editar" % id, com_fotos=True,\n'
        '                mostrar_contratante=True, contratantes=db.list_contratantes(),\n'
        '                message=erro_doc, message_type="error")\n'
        '        ',
    )
    if t2 != t:
        app.write_text(t2, encoding="utf-8")
        print("app.py saves wrapped")
    else:
        print("app.py no change needed")
else:
    print("app.py missing")
print("patch done")
