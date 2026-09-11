#!/usr/bin/env python3
"""Patch runtime files on Render for contratados + watermark support."""
from pathlib import Path

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
        t2 = t2.replace(
            '"documento", "email", "celular", "whatsapp",\n        ])\n        if not data["nome"]:',
            '"documento", "email", "celular", "whatsapp", "contratante_id",\n        ])\n        if data.get("contratante_id"):\n            try:\n                data["contratante_id"] = int(data["contratante_id"])\n            except (TypeError, ValueError):\n                data["contratante_id"] = None\n        if not data["nome"]:',
        )
        t2 = t2.replace(
            '"documento", "email", "celular", "whatsapp",\n        ])\n        foto_doc = salvar_upload("foto_documento", "doc_pessoal")',
            '"documento", "email", "celular", "whatsapp", "contratante_id",\n        ])\n        if data.get("contratante_id"):\n            try:\n                data["contratante_id"] = int(data["contratante_id"])\n            except (TypeError, ValueError):\n                data["contratante_id"] = None\n        foto_doc = salvar_upload("foto_documento", "doc_pessoal")',
        )
        if t2 != t:
            app.write_text(t2, encoding="utf-8")
            print("app.py patched")
        else:
            print("app.py pattern mismatch")
    else:
        print("app.py already OK")
else:
    print("app.py missing")

dbp = Path("database.py")
if dbp.exists():
    t = dbp.read_text(encoding="utf-8")
    chunk = t.split("def list_contratados")[1][:1200] if "def list_contratados" in t else ""
    if "contratante_nome" not in chunk:
        if 'sql = "SELECT * FROM contratado"' in t:
            t = t.replace(
                'sql = "SELECT * FROM contratado"',
                'sql = "SELECT cd.*, ct.nome AS contratante_nome FROM contratado cd LEFT JOIN contratante ct ON cd.contratante_id = ct.id"',
                1,
            )
            t = t.replace("ORDER BY nome", "ORDER BY cd.nome", 1)
            t = t.replace('where.append("contratante_id = ?")', 'where.append("cd.contratante_id = ?")')
            t = t.replace('where.append("(nome LIKE ? OR documento LIKE ?)")', 'where.append("(cd.nome LIKE ? OR cd.documento LIKE ?)")')
            dbp.write_text(t, encoding="utf-8")
            print("database.py patched")
        else:
            print("database pattern not found")
    else:
        print("database.py already OK")
print("patch done")
