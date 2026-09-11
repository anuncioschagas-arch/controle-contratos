#!/usr/bin/env python3
"""Garante select de contratante e operador no form de contratado."""
from pathlib import Path
import re

FIXED_NOVO = '''
@app.route("/contratados/novo", method=["GET", "POST"])
def novo_contratado():
    contratantes = db.list_contratantes()
    operadores = db.list_operadores() if hasattr(db, "list_operadores") else []
    user = usuario_atual()
    mostrar_op = bool(user and user.get("perfil") == "admin")
    if request.method == "POST":
        data = form_to_dict([
            "nome", "cep", "logradouro", "numero", "bairro", "cidade", "uf",
            "documento", "email", "celular", "whatsapp", "contratante_id", "operador_id",
        ])
        if data.get("contratante_id"):
            try:
                data["contratante_id"] = int(data["contratante_id"])
            except (TypeError, ValueError):
                data["contratante_id"] = None
        if data.get("operador_id"):
            try:
                data["operador_id"] = int(data["operador_id"])
            except (TypeError, ValueError):
                data["operador_id"] = None
        if not mostrar_op:
            data["operador_id"] = None
        if not data["nome"]:
            return render(
                "form_pessoa.html",
                titulo="Novo Contratado",
                item=data,
                base_url="/contratados",
                action="/contratados/novo",
                com_fotos=True,
                mostrar_contratante=True,
                contratantes=contratantes,
                mostrar_operador=mostrar_op,
                operadores=operadores,
                message="Nome é obrigatório.",
                message_type="error",
            )
        foto_doc = salvar_upload("foto_documento", "doc_pessoal")
        foto_comp = salvar_upload("foto_comprovante", "comp_residencia")
        if foto_doc:
            data["foto_documento"] = foto_doc
        if foto_comp:
            data["foto_comprovante"] = foto_comp
        if not data.get("contratante_id"):
            data = forcar_contratante_no_data(data)
        erro_doc = None
        try:
            erro_doc = verificar_documento_unico(data.get("documento"))
        except Exception:
            erro_doc = None
        if erro_doc:
            return render(
                "form_pessoa.html",
                titulo="Novo Contratado",
                item=data,
                base_url="/contratados",
                action="/contratados/novo",
                com_fotos=True,
                mostrar_contratante=True,
                contratantes=contratantes,
                mostrar_operador=mostrar_op,
                operadores=operadores,
                message=erro_doc,
                message_type="error",
            )
        try:
            db.save_contratado(data)
        except Exception as e:
            if "DocumentoDuplicado" in type(e).__name__ or "duplic" in str(e).lower():
                return render(
                    "form_pessoa.html",
                    titulo="Novo Contratado",
                    item=data,
                    base_url="/contratados",
                    action="/contratados/novo",
                    com_fotos=True,
                    mostrar_contratante=True,
                    contratantes=contratantes,
                    mostrar_operador=mostrar_op,
                    operadores=operadores,
                    message=str(e),
                    message_type="error",
                )
            raise
        return redirect("/contratados")
    return render(
        "form_pessoa.html",
        titulo="Novo Contratado",
        item=None,
        base_url="/contratados",
        action="/contratados/novo",
        com_fotos=True,
        mostrar_contratante=True,
        contratantes=contratantes,
        mostrar_operador=mostrar_op,
        operadores=operadores,
    )
'''

FIXED_EDIT = '''
@app.route("/contratados/<id:int>/editar", method=["GET", "POST"])
def editar_contratado(id):
    item = db.get_contratado(id)
    if not item:
        raise HTTPError(404, "Contratado não encontrado")
    cid = escopo_contratante_id()
    if cid and item.get("contratante_id") and int(item["contratante_id"]) != int(cid):
        raise HTTPError(403, "Acesso negado a este contratado.")
    contratantes = db.list_contratantes()
    operadores = db.list_operadores() if hasattr(db, "list_operadores") else []
    user = usuario_atual()
    mostrar_op = bool(user and user.get("perfil") == "admin")
    if request.method == "POST":
        data = form_to_dict([
            "nome", "cep", "logradouro", "numero", "bairro", "cidade", "uf",
            "documento", "email", "celular", "whatsapp", "contratante_id", "operador_id",
        ])
        if data.get("contratante_id"):
            try:
                data["contratante_id"] = int(data["contratante_id"])
            except (TypeError, ValueError):
                data["contratante_id"] = None
        if data.get("operador_id"):
            try:
                data["operador_id"] = int(data["operador_id"])
            except (TypeError, ValueError):
                data["operador_id"] = None
        if not mostrar_op:
            data["operador_id"] = item.get("operador_id")
        foto_doc = salvar_upload("foto_documento", "doc_pessoal")
        foto_comp = salvar_upload("foto_comprovante", "comp_residencia")
        if foto_doc:
            data["foto_documento"] = foto_doc
        if foto_comp:
            data["foto_comprovante"] = foto_comp
        if not data.get("contratante_id"):
            data = forcar_contratante_no_data(data)
        if cid and item.get("contratante_id") and int(item["contratante_id"]) != int(cid):
            raise HTTPError(403, "Acesso negado a este contratado.")
        erro_doc = None
        try:
            erro_doc = verificar_documento_unico(data.get("documento"), excluir_contratado_id=id)
        except Exception:
            erro_doc = None
        if erro_doc:
            return render(
                "form_pessoa.html",
                titulo="Editar Contratado",
                item=data,
                base_url="/contratados",
                action="/contratados/%d/editar" % id,
                com_fotos=True,
                mostrar_contratante=True,
                contratantes=contratantes,
                mostrar_operador=mostrar_op,
                operadores=operadores,
                message=erro_doc,
                message_type="error",
            )
        try:
            db.save_contratado(data, id=id)
        except Exception as e:
            if "DocumentoDuplicado" in type(e).__name__ or "duplic" in str(e).lower():
                return render(
                    "form_pessoa.html",
                    titulo="Editar Contratado",
                    item=data,
                    base_url="/contratados",
                    action="/contratados/%d/editar" % id,
                    com_fotos=True,
                    mostrar_contratante=True,
                    contratantes=contratantes,
                    mostrar_operador=mostrar_op,
                    operadores=operadores,
                    message=str(e),
                    message_type="error",
                )
            raise
        return redirect("/contratados")
    return render(
        "form_pessoa.html",
        titulo="Editar Contratado",
        item=item,
        base_url="/contratados",
        action="/contratados/%d/editar" % id,
        com_fotos=True,
        mostrar_contratante=True,
        contratantes=contratantes,
        mostrar_operador=mostrar_op,
        operadores=operadores,
    )
'''

dbp = Path("database.py")
if dbp.exists():
    t = dbp.read_text(encoding="utf-8")
    if "ADD COLUMN operador_id" not in t:
        mig = '''
        if not _coluna_existe(cur, "contratado", "operador_id"):
            cur.execute("ALTER TABLE contratado ADD COLUMN operador_id INTEGER")
'''
        if "foto_comprovante" in t:
            p = t.find("ADD COLUMN foto_comprovante")
            if p > 0:
                p = t.find("\n", p) + 1
                t = t[:p] + mig + t[p:]
                print("operador_id migration")
        elif "CREATE TABLE IF NOT EXISTS contratado" in t:
            p = t.find("CREATE TABLE IF NOT EXISTS contratado")
            p2 = t.find('""")', p)
            p2 = t.find("\n", p2) + 1
            t = t[:p2] + mig + t[p2:]
            print("operador_id migration after create")
    if "def list_operadores" not in t:
        t = t.rstrip() + '''

def list_operadores():
    with db_session() as conn:
        rows = conn.execute(
            "SELECT id, nome, login, perfil, contratante_id, setor_id FROM usuario WHERE ativo = 1 AND perfil IN ('operador', 'admin') ORDER BY nome"
        ).fetchall()
        return [dict(r) for r in rows]
'''
        print("list_operadores")
    if "operador_id=?" not in t[t.find("def save_contratado"):t.find("def save_contratado")+900]:
        t = t.replace(
            "foto_documento=?, foto_comprovante=?, contratante_id=?\n                WHERE id=?",
            "foto_documento=?, foto_comprovante=?, contratante_id=?, operador_id=?\n                WHERE id=?",
        )
        t = t.replace(
            'data.get("whatsapp"), foto_doc, foto_comp, data.get("contratante_id"), id',
            'data.get("whatsapp"), foto_doc, foto_comp, data.get("contratante_id"), data.get("operador_id"), id',
        )
        t = t.replace(
            """(nome, cep, logradouro, numero, bairro, cidade, uf, documento, email, celular, whatsapp,\n                     foto_documento, foto_comprovante, contratante_id)\n                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            """(nome, cep, logradouro, numero, bairro, cidade, uf, documento, email, celular, whatsapp,\n                     foto_documento, foto_comprovante, contratante_id, operador_id)\n                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        )
        t = t.replace(
            'data.get("whatsapp"), data.get("foto_documento"), data.get("foto_comprovante"),\n                data.get("contratante_id")',
            'data.get("whatsapp"), data.get("foto_documento"), data.get("foto_comprovante"),\n                data.get("contratante_id"), data.get("operador_id")',
        )
        print("save_contratado operador")
    if "operador_nome" not in t[t.find("def list_contratados"):t.find("def list_contratados")+500]:
        t = t.replace(
            '"SELECT cd.*, ct.nome AS contratante_nome "\n            "FROM contratado cd "\n            "LEFT JOIN contratante ct ON cd.contratante_id = ct.id"',
            '"SELECT cd.*, ct.nome AS contratante_nome, op.nome AS operador_nome "\n            "FROM contratado cd "\n            "LEFT JOIN contratante ct ON cd.contratante_id = ct.id "\n            "LEFT JOIN usuario op ON cd.operador_id = op.id"',
        )
        print("list join")
    if "operador_nome" not in t[t.find("def get_contratado"):t.find("def get_contratado")+400]:
        t = t.replace(
            """SELECT cd.*, ct.nome AS contratante_nome\n            FROM contratado cd\n            LEFT JOIN contratante ct ON cd.contratante_id = ct.id\n            WHERE cd.id = ?""",
            """SELECT cd.*, ct.nome AS contratante_nome, op.nome AS operador_nome\n            FROM contratado cd\n            LEFT JOIN contratante ct ON cd.contratante_id = ct.id\n            LEFT JOIN usuario op ON cd.operador_id = op.id\n            WHERE cd.id = ?""",
        )
        print("get join")
    dbp.write_text(t, encoding="utf-8")

form = Path("templates/form_pessoa.html")
if form.exists():
    f = form.read_text(encoding="utf-8")
    if "mostrar_operador" not in f:
        block = '''
            {% if mostrar_operador %}
            <div class="form-group full">
                <label>Operador responsável</label>
                <select name="operador_id" id="campo-operador">
                    <option value="">— Selecione o operador —</option>
                    {% for op in operadores or [] %}
                    <option value="{{ op.id }}"
                        {% if item and item.operador_id and item.operador_id|int == op.id|int %}selected{% endif %}>
                        #{{ op.id }} — {{ op.nome }} ({{ op.perfil }})
                    </option>
                    {% endfor %}
                </select>
                <small style="color:#718096; font-size:0.8rem;">Somente o administrador define ou altera o operador vinculado a este contratado.</small>
            </div>
            {% endif %}
'''
        if "{% if mostrar_contratante %}" in f:
            f = re.sub(
                r"(\{% if mostrar_contratante %\}.*?\{% endif %\})",
                r"\1\n" + block,
                f,
                count=1,
                flags=re.S,
            )
            form.write_text(f, encoding="utf-8")
            print("form operador block")

lp = Path("templates/list_pessoa.html")
if lp.exists():
    f = lp.read_text(encoding="utf-8")
    if "Operador" not in f and "Contratante" in f:
        f = f.replace(
            "<th>Contratante</th>",
            "<th>Contratante</th>\n                    <th>Operador</th>",
        )
        if "item.contratante_id" in f and "operador_nome" not in f:
            f = f.replace(
                """{% if item.contratante_id %}\n                        #{{ item.contratante_id }}{% if item.contratante_nome %} — {{ item.contratante_nome }}{% endif %}\n                        {% else %}—{% endif %}\n                    </td>\n                    {% endif %}\n""",
                """{% if item.contratante_id %}\n                        #{{ item.contratante_id }}{% if item.contratante_nome %} — {{ item.contratante_nome }}{% endif %}\n                        {% else %}—{% endif %}\n                    </td>\n                    <td>{{ item.operador_nome or '—' }}</td>\n                    {% endif %}\n""",
            )
        lp.write_text(f, encoding="utf-8")
        print("list operador col")

app = Path("app.py")
if app.exists():
    t = app.read_text(encoding="utf-8")

    def replace_route(src, name, new_block):
        pattern = rf'(?:@app\.route\([^\n]+\)\n)+def {name}\(.*?(?=\n@app\.route|\n# =====|\nif __name__)'
        m = re.search(pattern, src, re.S)
        if not m:
            m2 = re.search(rf'def {name}\(.*?(?=\n@app\.route|\n# =====|\nif __name__)', src, re.S)
            if not m2:
                print(name, "NOT FOUND")
                return src
            start = m2.start()
            while start > 0 and src.rfind("@app.route", 0, start) > src.rfind("\ndef ", 0, start):
                start = src.rfind("@app.route", 0, start)
            end = m2.end()
            src = src[:start] + new_block.strip() + "\n\n" + src[end:]
            print(name, "replaced (alt)")
            return src
        src = src[: m.start()] + new_block.strip() + "\n\n" + src[m.end() :]
        print(name, "replaced")
        return src

    t = replace_route(t, "novo_contratado", FIXED_NOVO)
    t = replace_route(t, "editar_contratado", FIXED_EDIT)
    app.write_text(t, encoding="utf-8")
    print("mostrar_operador", t.count("mostrar_operador"))
print("fix_contratante_form done")
