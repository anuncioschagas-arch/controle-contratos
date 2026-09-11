#!/usr/bin/env python3
"""Corrige 500 em /contratos/<id>/editar e inclui operador no form."""
from pathlib import Path
import re

dbp = Path("database.py")
if dbp.exists():
    t = dbp.read_text(encoding="utf-8")
    new_get = '''
def get_contrato(id):
    with db_session() as conn:
        try:
            cols = [r[1] for r in conn.execute("PRAGMA table_info(contrato)").fetchall()]
            if "operador_id" not in cols:
                conn.execute("ALTER TABLE contrato ADD COLUMN operador_id INTEGER")
        except Exception:
            pass
        try:
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
        except Exception:
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
                       s.nome AS setor_nome, s.responsavel AS setor_responsavel
                FROM contrato c
                LEFT JOIN contratante ct ON c.contratante_id = ct.id
                LEFT JOIN contratado cd ON c.contratado_id = cd.id
                LEFT JOIN setor s ON c.setor_id = s.id
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
        print("get_contrato safe")
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
        print("save operador")
    dbp.write_text(t, encoding="utf-8")

FIXED_NOVO = '''
@app.route("/contratos/novo", method=["GET", "POST"])
def novo_contrato():
    contratantes, contratados, setores = _listas_para_contrato()
    try:
        operadores = db.list_operadores() if hasattr(db, "list_operadores") else []
    except Exception:
        operadores = []
    if request.method == "POST":
        data = form_to_dict([
            "numero", "contratante_id", "contratado_id", "setor_id", "operador_id",
            "objeto", "valor", "data_inicio", "data_fim", "status", "observacoes",
        ])
        data["contratante_id"] = int(data["contratante_id"]) if data.get("contratante_id") else None
        data["contratado_id"] = int(data["contratado_id"]) if data.get("contratado_id") else None
        data["setor_id"] = int(data["setor_id"]) if data.get("setor_id") else None
        data["operador_id"] = int(data["operador_id"]) if data.get("operador_id") else None
        data = forcar_vinculos_no_data(data)
        try:
            data["valor"] = float(data["valor"]) if data.get("valor") else 0
        except ValueError:
            data["valor"] = 0
        if not data.get("numero") or not data.get("contratante_id") or not data.get("contratado_id") or not data.get("objeto"):
            return render(
                "form_contrato.html",
                titulo="Novo Contrato",
                item=data,
                action="/contratos/novo",
                contratantes=contratantes,
                contratados=contratados,
                setores=setores,
                operadores=operadores,
                numero_sugerido=db.next_numero_contrato(),
                message="Preencha os campos obrigatórios.",
                message_type="error",
            )
        try:
            db.save_contrato(data)
        except Exception as e:
            return render(
                "form_contrato.html",
                titulo="Novo Contrato",
                item=data,
                action="/contratos/novo",
                contratantes=contratantes,
                contratados=contratados,
                setores=setores,
                operadores=operadores,
                numero_sugerido=data.get("numero") or db.next_numero_contrato(),
                message="Erro ao salvar: %s" % e,
                message_type="error",
            )
        return redirect("/contratos")
    return render(
        "form_contrato.html",
        titulo="Novo Contrato",
        item=None,
        action="/contratos/novo",
        contratantes=contratantes,
        contratados=contratados,
        setores=setores,
        operadores=operadores,
        numero_sugerido=db.next_numero_contrato(),
    )


'''

FIXED_EDIT = '''
@app.route("/contratos/<id:int>/editar", method=["GET", "POST"])
def editar_contrato(id):
    try:
        item = db.get_contrato(id)
    except Exception as e:
        raise HTTPError(500, "Erro ao carregar contrato: %s" % e)
    if not item:
        raise HTTPError(404, "Contrato não encontrado")
    _garantir_acesso_contrato(item)
    contratantes, contratados, setores = _listas_para_contrato()
    try:
        operadores = db.list_operadores() if hasattr(db, "list_operadores") else []
    except Exception:
        operadores = []
    if request.method == "POST":
        data = form_to_dict([
            "numero", "contratante_id", "contratado_id", "setor_id", "operador_id",
            "objeto", "valor", "data_inicio", "data_fim", "status", "observacoes",
        ])
        data["contratante_id"] = int(data["contratante_id"]) if data.get("contratante_id") else None
        data["contratado_id"] = int(data["contratado_id"]) if data.get("contratado_id") else None
        data["setor_id"] = int(data["setor_id"]) if data.get("setor_id") else None
        data["operador_id"] = int(data["operador_id"]) if data.get("operador_id") else None
        data = forcar_vinculos_no_data(data)
        try:
            data["valor"] = float(data["valor"]) if data.get("valor") else 0
        except ValueError:
            data["valor"] = 0
        try:
            db.save_contrato(data, id=id)
        except Exception as e:
            data["id"] = id
            return render(
                "form_contrato.html",
                titulo="Editar Contrato %s" % (item.get("numero") or id),
                item=data,
                action="/contratos/%d/editar" % id,
                contratantes=contratantes,
                contratados=contratados,
                setores=setores,
                operadores=operadores,
                numero_sugerido=data.get("numero"),
                message="Erro ao salvar: %s" % e,
                message_type="error",
            )
        return redirect("/contratos/%d" % id)
    return render(
        "form_contrato.html",
        titulo="Editar Contrato %s" % item["numero"],
        item=item,
        action="/contratos/%d/editar" % id,
        contratantes=contratantes,
        contratados=contratados,
        setores=setores,
        operadores=operadores,
        numero_sugerido=item["numero"],
    )


'''

app = Path("app.py")
if app.exists():
    t = app.read_text(encoding="utf-8")
    start2 = t.find("def novo_contrato(")
    if start2 > 0:
        start_dec = t.rfind("@app.route", 0, start2)
        start = start_dec if start_dec >= 0 else start2
        rest = t[start2 + 4 :]
        m = re.search(r"\n@app\.route\(", rest)
        if m:
            end = start2 + 4 + m.start()
            t = t[:start] + FIXED_NOVO + t[end:]
            print("novo_contrato replaced")
    start2 = t.find("def editar_contrato(")
    if start2 > 0:
        start_dec = t.rfind("@app.route", 0, start2)
        start = start_dec if start_dec >= 0 else start2
        rest = t[start2 + 4 :]
        m = re.search(r"\n@app\.route\(", rest)
        if m:
            end = start2 + 4 + m.start()
            t = t[:start] + FIXED_EDIT + t[end:]
            print("editar_contrato replaced")
    t = t.replace(
        'return render("ver_contrato.html", c=c)',
        'return render("ver_contrato.html", c=c, item=c)',
    )
    app.write_text(t, encoding="utf-8")
    print("app written")

form = Path("templates/form_contrato.html")
if form.exists():
    f = form.read_text(encoding="utf-8")
    f = f.replace(
        "{% if item and item.operador_id and item.operador_id|int == op.id|int %}selected{% endif %}",
        "{% if item and item.operador_id and (item.operador_id == op.id or item.operador_id|string == op.id|string) %}selected{% endif %}",
    )
    if "campo-operador-contrato" not in f:
        block = '''
            <div class="form-group">
                <label>Operador responsável</label>
                <select name="operador_id" id="campo-operador-contrato">
                    <option value="">— Selecione o operador —</option>
                    {% for op in operadores or [] %}
                    <option value="{{ op.id }}"
                        {% if item and item.operador_id and (item.operador_id == op.id or item.operador_id|string == op.id|string) %}selected{% endif %}>
                        #{{ op.id }} — {{ op.nome }}
                    </option>
                    {% endfor %}
                </select>
            </div>
'''
        if "<label>Valor Total (R$) *</label>" in f:
            f = f.replace("<label>Valor Total (R$) *</label>", block + "\n                <label>Valor Total (R$) *</label>", 1)
    form.write_text(f, encoding="utf-8")
    print("form ok")

print("fix_editar_contrato done")
