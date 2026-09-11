#!/usr/bin/env python3
"""Filtros de consulta: contratante, contratado e operador."""
from pathlib import Path
import re

dbp = Path("database.py")
if dbp.exists():
    t = dbp.read_text(encoding="utf-8")
    if "contratado_id=None" not in t[t.find("def consultar_contratos"): t.find("def consultar_contratos") + 220]:
        start = t.find("def consultar_contratos(")
        if start >= 0:
            rest = t[start + 4 :]
            m = re.search(r"\ndef ", rest)
            end = start + 4 + m.start() if m else len(t)
            new_fn = '''
def consultar_contratos(status=None, setor_id=None, vencimento_de=None, vencimento_ate=None,
                        vencimento_preset=None, contratante_id=None, contratado_id=None,
                        operador_id=None):
    from datetime import date, timedelta
    hoje = date.today()
    params = []
    where = []
    if vencimento_preset and not (vencimento_de or vencimento_ate):
        if vencimento_preset == "vencidos":
            where.append("c.data_fim IS NOT NULL AND c.data_fim < ?")
            params.append(hoje.isoformat())
        elif vencimento_preset == "mes":
            inicio_mes = hoje.replace(day=1)
            if hoje.month == 12:
                fim_mes = hoje.replace(year=hoje.year + 1, month=1, day=1) - timedelta(days=1)
            else:
                fim_mes = hoje.replace(month=hoje.month + 1, day=1) - timedelta(days=1)
            where.append("c.data_fim IS NOT NULL AND c.data_fim >= ? AND c.data_fim <= ?")
            params.extend([inicio_mes.isoformat(), fim_mes.isoformat()])
        elif vencimento_preset in ("30", "60", "90"):
            dias = int(vencimento_preset)
            limite = hoje + timedelta(days=dias)
            where.append("c.data_fim IS NOT NULL AND c.data_fim >= ? AND c.data_fim <= ?")
            params.extend([hoje.isoformat(), limite.isoformat()])
    if status:
        where.append("c.status = ?")
        params.append(status)
    if setor_id:
        where.append("c.setor_id = ?")
        params.append(int(setor_id))
    if contratante_id:
        where.append("c.contratante_id = ?")
        params.append(int(contratante_id))
    if contratado_id:
        where.append("c.contratado_id = ?")
        params.append(int(contratado_id))
    if operador_id:
        where.append("c.operador_id = ?")
        params.append(int(operador_id))
    if vencimento_de:
        where.append("c.data_fim IS NOT NULL AND c.data_fim >= ?")
        params.append(vencimento_de[:10])
    if vencimento_ate:
        where.append("c.data_fim IS NOT NULL AND c.data_fim <= ?")
        params.append(vencimento_ate[:10])
    sql = """
        SELECT c.*,
               ct.nome AS contratante_nome,
               cd.nome AS contratado_nome,
               s.nome AS setor_nome,
               op.nome AS operador_nome
        FROM contrato c
        LEFT JOIN contratante ct ON c.contratante_id = ct.id
        LEFT JOIN contratado cd ON c.contratado_id = cd.id
        LEFT JOIN setor s ON c.setor_id = s.id
        LEFT JOIN usuario op ON c.operador_id = op.id
    """
    if where:
        sql += " WHERE " + " AND ".join(where)
    sql += " ORDER BY c.data_fim ASC, c.id DESC"
    with db_session() as conn:
        try:
            cols = [r[1] for r in conn.execute("PRAGMA table_info(contrato)").fetchall()]
            if "operador_id" not in cols:
                conn.execute("ALTER TABLE contrato ADD COLUMN operador_id INTEGER")
        except Exception:
            pass
        try:
            rows = conn.execute(sql, params).fetchall()
        except Exception:
            sql = """
        SELECT c.*,
               ct.nome AS contratante_nome,
               cd.nome AS contratado_nome,
               s.nome AS setor_nome
        FROM contrato c
        LEFT JOIN contratante ct ON c.contratante_id = ct.id
        LEFT JOIN contratado cd ON c.contratado_id = cd.id
        LEFT JOIN setor s ON c.setor_id = s.id
    """
            where2 = [w for w in where if "operador_id" not in w]
            params2 = list(params)
            if operador_id and params2:
                params2 = params2[:-1]
            if where2:
                sql += " WHERE " + " AND ".join(where2)
            sql += " ORDER BY c.data_fim ASC, c.id DESC"
            rows = conn.execute(sql, params2 if where2 else []).fetchall()
        return [dict(r) for r in rows]
'''
            t = t[:start] + new_fn.strip() + "\n\n" + t[end + 1 :]
            dbp.write_text(t, encoding="utf-8")
            print("consultar_contratos updated")
    else:
        print("consultar already has contratado_id")

app = Path("app.py")
if app.exists():
    t = app.read_text(encoding="utf-8")
    if 'request.query.get("contratado_id"' not in t:
        t = t.replace(
            'vencimento_preset = request.query.get("vencimento_preset", "").strip() or None\n    return {\n        "status": status,\n        "setor_id": setor_id,\n        "vencimento_de": vencimento_de,\n        "vencimento_ate": vencimento_ate,\n        "vencimento_preset": vencimento_preset,\n    }',
            'contratante_id = request.query.get("contratante_id", "").strip() or None\n    contratado_id = request.query.get("contratado_id", "").strip() or None\n    operador_id = request.query.get("operador_id", "").strip() or None\n    vencimento_preset = request.query.get("vencimento_preset", "").strip() or None\n    return {\n        "status": status,\n        "setor_id": setor_id,\n        "contratante_id": contratante_id,\n        "contratado_id": contratado_id,\n        "operador_id": operador_id,\n        "vencimento_de": vencimento_de,\n        "vencimento_ate": vencimento_ate,\n        "vencimento_preset": vencimento_preset,\n    }',
        )
        print("filtros request")
    if "contratados=contratados" not in t:
        start = t.find("def consultas(")
        if start > 0:
            m = re.search(r"\n@app\.route\(", t[start:])
            end = start + m.start() if m else -1
            if end > start:
                block = '''
def consultas():
    filtros = _filtros_consulta_da_request()
    cid = escopo_contratante_id()
    sid = escopo_setor_id()
    setor_filtro = sid if sid else filtros.get("setor_id")
    contratante_filtro = cid if cid else filtros.get("contratante_id")
    itens = db.consultar_contratos(
        status=filtros.get("status"),
        setor_id=setor_filtro,
        vencimento_de=filtros.get("vencimento_de"),
        vencimento_ate=filtros.get("vencimento_ate"),
        vencimento_preset=filtros.get("vencimento_preset"),
        contratante_id=contratante_filtro,
        contratado_id=filtros.get("contratado_id"),
        operador_id=filtros.get("operador_id"),
    )
    setores = db.list_setores(contratante_id=cid)
    try:
        contratantes = db.list_contratantes() if not cid else [c for c in db.list_contratantes() if c["id"] == int(cid)]
    except Exception:
        contratantes = db.list_contratantes()
    try:
        contratados = db.list_contratados(contratante_id=cid) if cid else db.list_contratados()
    except Exception:
        contratados = db.list_contratados()
    try:
        operadores = db.list_operadores() if hasattr(db, "list_operadores") else []
    except Exception:
        operadores = []
    from datetime import date
    return render(
        "consultas.html",
        itens=itens,
        setores=setores,
        contratantes=contratantes,
        contratados=contratados,
        operadores=operadores,
        filtros=filtros,
        query_string=_query_string_filtros(filtros),
        hoje=date.today().isoformat(),
    )

'''
                t = t[:start] + block + t[end:]
                print("consultas route rewritten")
    if 'contratado_id=filtros.get("contratado_id")' not in t:
        t = t.replace(
            "contratante_id=cid,\n    )\n    if not PDF_DISPONIVEL:",
            'contratante_id=(cid if cid else filtros.get("contratante_id")),\n        contratado_id=filtros.get("contratado_id"),\n        operador_id=filtros.get("operador_id"),\n    )\n    if not PDF_DISPONIVEL:',
        )
        print("pdf kwargs")
    app.write_text(t, encoding="utf-8")

print("template assumed from repo")
print("fix_consultas_filtros done")
