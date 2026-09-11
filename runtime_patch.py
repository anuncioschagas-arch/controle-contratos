#!/usr/bin/env python3
"""Corrige list_contratados (SQL sem coluna ambigua) no boot do Render."""
from pathlib import Path
import re

FIXED = '''
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

dbp = Path("database.py")
if dbp.exists():
    t = dbp.read_text(encoding="utf-8")
    m = re.search(r"^def list_contratados\(.*?(?=^def )", t, re.M | re.S)
    if m:
        t = t[: m.start()] + FIXED.strip() + "\n\n" + t[m.end() :]
        dbp.write_text(t, encoding="utf-8")
        print("database.py list_contratados fixed")
    else:
        print("list_contratados not found for patch")
else:
    print("database.py missing")

app = Path("app.py")
if app.exists():
    t = app.read_text(encoding="utf-8")
    if "mostrar_contratante=True" not in t:
        t2 = t.replace(
            'action="/contratados/novo",\n        com_fotos=True,',
            'action="/contratados/novo",\n        com_fotos=True,\n        mostrar_contratante=True,\n        contratantes=db.list_contratantes(),',
        )
        t2 = t2.replace(
            'action="/contratados/%d/editar" % id,\n        com_fotos=True,',
            'action="/contratados/%d/editar" % id,\n        com_fotos=True,\n        mostrar_contratante=True,\n        contratantes=db.list_contratantes(),',
        )
        if t2 != t:
            app.write_text(t2, encoding="utf-8")
            print("app.py patched")
        else:
            print("app.py pattern mismatch")
    else:
        print("app.py already OK")
print("patch done")
