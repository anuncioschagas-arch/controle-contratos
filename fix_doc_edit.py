#!/usr/bin/env python3
"""Na edicao, nao tratar o proprio CPF/CNPJ como duplicado."""
from pathlib import Path
import re

NEW_FN = '''
def verificar_documento_unico(documento, excluir_contratante_id=None, excluir_contratado_id=None):
    """Impede CPF/CNPJ duplicado. Na edicao, informe excluir_*_id para ignorar o proprio registro."""
    digits = re.sub(r"\\D", "", str(documento or ""))
    if not digits or len(digits) < 11:
        return None

    def _mesmo_id(a, b):
        if a is None or b is None or a == "" or b == "":
            return False
        try:
            return int(a) == int(b)
        except (TypeError, ValueError):
            return False

    try:
        import sqlite3
        from database import DB_PATH
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        for r in conn.execute("SELECT id, nome, documento FROM contratante"):
            if _mesmo_id(r["id"], excluir_contratante_id):
                continue
            if re.sub(r"\\D", "", str(r["documento"] or "")) == digits:
                conn.close()
                return "CPF/CNPJ já cadastrado no CONTRATANTE #%s — %s. Não é permitido duplicar." % (r["id"], r["nome"] or "")
        for r in conn.execute("SELECT id, nome, documento FROM contratado"):
            if _mesmo_id(r["id"], excluir_contratado_id):
                continue
            if re.sub(r"\\D", "", str(r["documento"] or "")) == digits:
                conn.close()
                return "CPF/CNPJ já cadastrado no CONTRATADO #%s — %s. Não é permitido duplicar." % (r["id"], r["nome"] or "")
        conn.close()
    except Exception:
        pass
    return None
'''

app = Path("app.py")
if app.exists():
    t = app.read_text(encoding="utf-8")
    if "import re\n" not in t[:1200] and "import re " not in t[:1200]:
        t = "import re\n" + t

    start = t.find("def verificar_documento_unico(")
    if start >= 0:
        rest = t[start + 4 :]
        m = re.search(r"\ndef ", rest)
        if m:
            end = start + 4 + m.start()
            t = t[:start] + NEW_FN.strip() + "\n\n" + t[end + 1 :]
            print("verificar replaced")
        else:
            t = t[:start] + NEW_FN.strip() + "\n"
            print("verificar replaced end")
    else:
        idx = t.find("@app.route")
        if idx > 0:
            t = t[:idx] + NEW_FN.strip() + "\n\n" + t[idx:]
            print("verificar inserted")

    start = t.find("def editar_contratado(")
    if start >= 0:
        m = re.search(r"\ndef ", t[start + 4 :])
        end = start + 4 + m.start() if m else len(t)
        block = t[start:end]
        if "verificar_documento_unico" in block:
            if "excluir_contratado_id=id" not in block:
                block2 = block.replace(
                    'verificar_documento_unico(data.get("documento"))',
                    'verificar_documento_unico(data.get("documento"), excluir_contratado_id=id)',
                )
                t = t[:start] + block2 + t[end:]
                print("editar_contratado exclude added")
            else:
                print("editar_contratado already excludes")

    start = t.find("def editar_contratante(")
    if start >= 0:
        m = re.search(r"\ndef ", t[start + 4 :])
        end = start + 4 + m.start() if m else len(t)
        block = t[start:end]
        if "verificar_documento_unico" in block and "excluir_contratante_id=id" not in block:
            block2 = block.replace(
                'verificar_documento_unico(data.get("documento"))',
                'verificar_documento_unico(data.get("documento"), excluir_contratante_id=id)',
            )
            t = t[:start] + block2 + t[end:]
            print("editar_contratante exclude added")

    app.write_text(t, encoding="utf-8")
    print("app patched")

dbp = Path("database.py")
if dbp.exists():
    t = dbp.read_text(encoding="utf-8")
    start = t.find("def documento_ja_existe(")
    if start >= 0 and "_mesmo_id" not in t[start : start + 900]:
        new_db = '''
def documento_ja_existe(documento, excluir_contratante_id=None, excluir_contratado_id=None):
    digits = re.sub(r"\\D", "", str(documento or ""))
    if not digits or len(digits) < 11:
        return None
    def _mesmo_id(a, b):
        if a is None or b is None or a == "" or b == "":
            return False
        try:
            return int(a) == int(b)
        except (TypeError, ValueError):
            return False
    with db_session() as conn:
        for r in conn.execute("SELECT id, nome, documento FROM contratante").fetchall():
            if _mesmo_id(r["id"], excluir_contratante_id):
                continue
            if re.sub(r"\\D", "", str(r["documento"] or "")) == digits:
                return {"tabela": "contratante", "id": r["id"], "nome": r["nome"]}
        for r in conn.execute("SELECT id, nome, documento FROM contratado").fetchall():
            if _mesmo_id(r["id"], excluir_contratado_id):
                continue
            if re.sub(r"\\D", "", str(r["documento"] or "")) == digits:
                return {"tabela": "contratado", "id": r["id"], "nome": r["nome"]}
    return None
'''
        rest = t[start + 4 :]
        m = re.search(r"\ndef ", rest)
        end = start + 4 + m.start() if m else len(t)
        t = t[:start] + new_db.strip() + "\n\n" + t[end + 1 :]
        if "import re" not in t[:400]:
            t = "import re\n" + t
        dbp.write_text(t, encoding="utf-8")
        print("database hardened")
    else:
        print("database ok")
print("fix_doc_edit done")
