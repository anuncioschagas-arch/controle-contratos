#!/usr/bin/env python3
"""Patches: list_contratados, operador/contratante, CPF/CNPJ unico."""
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

DOC_HELPER = '''
def normalizar_documento(doc):
    """Mantém só dígitos do CPF/CNPJ."""
    if not doc:
        return ""
    return re.sub(r"\\D", "", str(doc))


class DocumentoDuplicado(Exception):
    """CPF/CNPJ já cadastrado em contratante ou contratado."""
    pass


def documento_ja_existe(documento, excluir_contratante_id=None, excluir_contratado_id=None):
    """Verifica se CPF/CNPJ já existe (compara só dígitos)."""
    digits = normalizar_documento(documento)
    if not digits or len(digits) < 11:
        return None
    with db_session() as conn:
        rows = conn.execute("SELECT id, nome, documento FROM contratante").fetchall()
        for r in rows:
            if excluir_contratante_id and int(r["id"]) == int(excluir_contratante_id):
                continue
            if normalizar_documento(r["documento"]) == digits:
                return {"tabela": "contratante", "id": r["id"], "nome": r["nome"]}
        rows = conn.execute("SELECT id, nome, documento FROM contratado").fetchall()
        for r in rows:
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
        if "import os" in t:
            t = t.replace("import os", "import os\nimport re", 1)
        else:
            t = "import re\n" + t
    if "def documento_ja_existe" not in t:
        t = t.replace(
            "def save_contratante(data, id=None):",
            DOC_HELPER + "def save_contratante(data, id=None):",
            1,
        )
        print("documento helper added")
    if "documento_ja_existe" not in t[t.find("def save_contratante"): t.find("def save_contratante") + 350]:
        t = t.replace(
            "def save_contratante(data, id=None):\n    with db_session() as conn:\n        if id:",
            "def save_contratante(data, id=None):\n"
            "    doc = data.get(\"documento\")\n"
            "    if doc:\n"
            "        dup = documento_ja_existe(doc, excluir_contratante_id=id)\n"
            "        if dup:\n"
            "            raise DocumentoDuplicado(\n"
            "                \"CPF/CNPJ já cadastrado em %s #%s — %s. Não é permitido duplicar.\"\n"
            "                % (dup[\"tabela\"], dup[\"id\"], dup[\"nome\"])\n"
            "            )\n"
            "    with db_session() as conn:\n"
            "        if id:",
            1,
        )
        print("save_contratante validated")
    if "def save_contratado" in t and "documento_ja_existe" not in t[t.find("def save_contratado"): t.find("def save_contratado") + 350]:
        t = re.sub(
            r"def save_contratado\(data, id=None\):\n    with db_session\(\) as conn:\n        if id:",
            "def save_contratado(data, id=None):\n"
            "    doc = data.get(\"documento\")\n"
            "    if doc:\n"
            "        dup = documento_ja_existe(doc, excluir_contratado_id=id)\n"
            "        if dup:\n"
            "            raise DocumentoDuplicado(\n"
            "                \"CPF/CNPJ já cadastrado em %s #%s — %s. Não é permitido duplicar.\"\n"
            "                % (dup[\"tabela\"], dup[\"id\"], dup[\"nome\"])\n"
            "            )\n"
            "    with db_session() as conn:\n"
            "        if id:",
            t,
            count=1,
        )
        print("save_contratado validated")
    m = re.search(r"^def list_contratados\(.*?(?=^def )", t, re.M | re.S)
    if m:
        t = t[: m.start()] + FIXED_LIST.strip() + "\n\n" + t[m.end() :]
        print("list_contratados replaced")
    dbp.write_text(t, encoding="utf-8")
else:
    print("database.py missing")

app = Path("app.py")
if app.exists():
    t = app.read_text(encoding="utf-8")
    changed = False
    if "DocumentoDuplicado" not in t:
        if 'db.save_contratante(data)\n        return redirect("/contratantes")' in t:
            t = t.replace(
                'db.save_contratante(data)\n        return redirect("/contratantes")',
                "try:\n"
                "            db.save_contratante(data)\n"
                "        except db.DocumentoDuplicado as e:\n"
                "            return render(\n"
                "                \"form_pessoa.html\",\n"
                "                titulo=\"Novo Contratante\",\n"
                "                item=data,\n"
                "                base_url=\"/contratantes\",\n"
                "                action=\"/contratantes/novo\",\n"
                "                message=str(e),\n"
                "                message_type=\"error\",\n"
                "            )\n"
                "        return redirect("/contratantes")",
                1,
            )
            changed = True
        if 'db.save_contratante(data, id=id)\n        return redirect("/contratantes")' in t:
            t = t.replace(
                'db.save_contratante(data, id=id)\n        return redirect("/contratantes")',
                "try:\n"
                "            db.save_contratante(data, id=id)\n"
                "        except db.DocumentoDuplicado as e:\n"
                "            return render(\n"
                "                \"form_pessoa.html\",\n"
                "                titulo=\"Editar Contratante\",\n"
                "                item=data,\n"
                "                base_url=\"/contratantes\",\n"
                "                action=\"/contratantes/%d/editar\" % id,\n"
                "                message=str(e),\n"
                "                message_type=\"error\",\n"
                "            )\n"
                "        return redirect("/contratantes")",
                1,
            )
            changed = True
        if 'db.save_contratado(data)\n        return redirect("/contratados")' in t:
            t = t.replace(
                'db.save_contratado(data)\n        return redirect("/contratados")',
                "try:\n"
                "            db.save_contratado(data)\n"
                "        except db.DocumentoDuplicado as e:\n"
                "            return render(\n"
                "                \"form_pessoa.html\",\n"
                "                titulo=\"Novo Contratado\",\n"
                "                item=data,\n"
                "                base_url=\"/contratados\",\n"
                "                action=\"/contratados/novo\",\n"
                "                com_fotos=True,\n"
                "                mostrar_contratante=True,\n"
                "                contratantes=db.list_contratantes(),\n"
                "                message=str(e),\n"
                "                message_type=\"error\",\n"
                "            )\n"
                "        return redirect("/contratados")",
                1,
            )
            changed = True
        if 'db.save_contratado(data, id=id)\n        return redirect("/contratados")' in t:
            t = t.replace(
                'db.save_contratado(data, id=id)\n        return redirect("/contratados")',
                "try:\n"
                "            db.save_contratado(data, id=id)\n"
                "        except db.DocumentoDuplicado as e:\n"
                "            return render(\n"
                "                \"form_pessoa.html\",\n"
                "                titulo=\"Editar Contratado\",\n"
                "                item=data,\n"
                "                base_url=\"/contratados\",\n"
                "                action=\"/contratados/%d/editar\" % id,\n"
                "                com_fotos=True,\n"
                "                mostrar_contratante=True,\n"
                "                contratantes=db.list_contratantes(),\n"
                "                message=str(e),\n"
                "                message_type=\"error\",\n"
                "            )\n"
                "        return redirect("/contratados")",
                1,
            )
            changed = True
    if changed:
        app.write_text(t, encoding="utf-8")
        print("app.py patched")
    else:
        print("app.py already OK")
print("patch done")
