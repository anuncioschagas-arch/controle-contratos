#!/usr/bin/env python3
"""Garante select de contratante no form de contratado (admin e operador)."""
from pathlib import Path
import re

FIXED_NOVO = '''
@app.route("/contratados/novo", method=["GET", "POST"])
def novo_contratado():
    contratantes = db.list_contratantes()
    if request.method == "POST":
        data = form_to_dict([
            "nome", "cep", "logradouro", "numero", "bairro", "cidade", "uf",
            "documento", "email", "celular", "whatsapp", "contratante_id",
        ])
        if data.get("contratante_id"):
            try:
                data["contratante_id"] = int(data["contratante_id"])
            except (TypeError, ValueError):
                data["contratante_id"] = None
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
    if request.method == "POST":
        data = form_to_dict([
            "nome", "cep", "logradouro", "numero", "bairro", "cidade", "uf",
            "documento", "email", "celular", "whatsapp", "contratante_id",
        ])
        if data.get("contratante_id"):
            try:
                data["contratante_id"] = int(data["contratante_id"])
            except (TypeError, ValueError):
                data["contratante_id"] = None
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
    )
'''

app = Path("app.py")
if not app.exists():
    print("app.py missing")
    raise SystemExit(0)

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
print("fix_contratante_form done")
print("mostrar count", t.count("mostrar_contratante=True"))
