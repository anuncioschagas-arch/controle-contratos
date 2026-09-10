#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sistema de Controle de Contratos
Tabelas: CONTRATANTE | CONTRATADO | SETOR | CONTRATO

Como executar:
  1) pip install -r requirements.txt
  2) python app.py
  3) Abra o navegador em http://127.0.0.1:8080
"""

import os
import sys

# ---------------------------------------------------------------------------
# Caminhos
# ---------------------------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

# ---------------------------------------------------------------------------
# Dependências com mensagens claras em português
# ---------------------------------------------------------------------------
def _erro_dependencia(nome, comando):
    print()
    print("=" * 60)
    print("  ERRO: biblioteca necessária não encontrada:", nome)
    print("=" * 60)
    print()
    print("  Execute no terminal (na pasta do projeto):")
    print()
    print("    " + comando)
    print()
    print("  Depois rode novamente:")
    print()
    print("    python app.py")
    print()
    print("=" * 60)
    sys.exit(1)


try:
    import bottle
    from bottle import Bottle, request, response, redirect, static_file, HTTPError
except ImportError:
    # bottle.py deve estar na mesma pasta
    bottle_path = os.path.join(BASE_DIR, "bottle.py")
    if not os.path.isfile(bottle_path):
        _erro_dependencia("bottle", "O arquivo bottle.py deve estar na mesma pasta do app.py")
    sys.path.insert(0, BASE_DIR)
    try:
        import bottle
        from bottle import Bottle, request, response, redirect, static_file, HTTPError
    except ImportError:
        _erro_dependencia("bottle", "Verifique se o arquivo bottle.py existe nesta pasta")

try:
    from jinja2 import Environment, FileSystemLoader, select_autoescape
except ImportError:
    _erro_dependencia("jinja2", "pip install jinja2")

# PDF é opcional (app funciona sem ele)
_PDF_ERRO = None
try:
    import reportlab  # noqa: F401
    from contrato_pdf import gerar_pdf_contrato, gerar_pdf_consulta
    PDF_DISPONIVEL = True
except Exception as e:
    PDF_DISPONIVEL = False
    _PDF_ERRO = str(e)

    def gerar_pdf_contrato(*args, **kwargs):
        raise RuntimeError(
            "Geração de PDF indisponível.\n"
            "1) Instale: pip install reportlab\n"
            "2) Reinicie o app (Ctrl+C e python app.py de novo)\n"
            "Detalhe técnico: " + str(e)
        )

    def gerar_pdf_consulta(*args, **kwargs):
        raise RuntimeError("Geração de PDF indisponível. " + str(e))

import database as db

# ---------------------------------------------------------------------------
# Configuração
# ---------------------------------------------------------------------------
TEMPLATE_DIR = os.path.join(BASE_DIR, "templates")
STATIC_DIR = os.path.join(BASE_DIR, "static")

app = Bottle()

jinja_env = Environment(
    loader=FileSystemLoader(TEMPLATE_DIR),
    autoescape=select_autoescape(["html", "xml"]),
)


def render(template_name, **context):
    template = jinja_env.get_template(template_name)
    return template.render(**context)



# ---------------------------------------------------------------------------
# Segurança: sessão por cookie assinado + perfis
# ---------------------------------------------------------------------------
import hashlib
import hmac
import json
import time

# Altere esta chave em produção!
SECRET_KEY = os.environ.get("CONTRATOS_SECRET", "contratos-segredo-altere-em-producao-2026")
SESSION_COOKIE = "contratos_sessao"
SESSION_MAX_AGE = 60 * 60 * 8  # 8 horas

# Rotas públicas (sem login)
PUBLIC_PATHS = {"/login", "/static"}


def _sign(payload: str) -> str:
    sig = hmac.new(SECRET_KEY.encode(), payload.encode(), hashlib.sha256).hexdigest()
    return payload + "." + sig


def _unsign(token: str):
    if not token or "." not in token:
        return None
    payload, sig = token.rsplit(".", 1)
    expected = hmac.new(SECRET_KEY.encode(), payload.encode(), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected, sig):
        return None
    return payload


def _criar_sessao(user: dict) -> str:
    data = {
        "id": user["id"],
        "nome": user["nome"],
        "login": user["login"],
        "perfil": user["perfil"],
        "contratante_id": user.get("contratante_id"),
        "setor_id": user.get("setor_id"),
        "exp": int(time.time()) + SESSION_MAX_AGE,
    }
    payload = json.dumps(data, separators=(",", ":"), ensure_ascii=False)
    # base64 simples via json em hex para evitar problemas de cookie
    import base64
    b64 = base64.urlsafe_b64encode(payload.encode()).decode()
    return _sign(b64)


def _ler_sessao():
    token = request.get_cookie(SESSION_COOKIE)
    if not token:
        return None
    b64 = _unsign(token)
    if not b64:
        return None
    try:
        import base64
        raw = base64.urlsafe_b64decode(b64.encode()).decode()
        data = json.loads(raw)
        if int(data.get("exp", 0)) < int(time.time()):
            return None
        return {
            "id": data["id"],
            "nome": data["nome"],
            "login": data["login"],
            "perfil": data["perfil"],
            "contratante_id": data.get("contratante_id"),
            "setor_id": data.get("setor_id"),
        }
    except Exception:
        return None


def usuario_atual():
    return _ler_sessao()


def escopo_contratante_id():
    """Retorna contratante_id do usuário (None = admin vê tudo)."""
    user = usuario_atual()
    if not user:
        return None
    if user.get("perfil") == "admin":
        return None
    cid = user.get("contratante_id")
    if cid is None or cid == "":
        return None
    try:
        return int(cid)
    except (TypeError, ValueError):
        return None


def escopo_setor_id():
    """Retorna setor_id do usuário (None = sem filtro de setor / admin)."""
    user = usuario_atual()
    if not user:
        return None
    if user.get("perfil") == "admin":
        return None
    sid = user.get("setor_id")
    if sid is None or sid == "":
        return None
    try:
        return int(sid)
    except (TypeError, ValueError):
        return None


def forcar_vinculos_no_data(data):
    """Operador/consulta: força contratante e setor vinculados."""
    cid = escopo_contratante_id()
    sid = escopo_setor_id()
    if cid:
        data["contratante_id"] = cid
    if sid:
        data["setor_id"] = sid
    return data


def forcar_contratante_no_data(data):
    """Compatibilidade: força só contratante (contratados)."""
    cid = escopo_contratante_id()
    if cid:
        data["contratante_id"] = cid
    return data




def render(template_name, **context):
    """Render Jinja com usuário da sessão."""
    context.setdefault("usuario", usuario_atual())
    template = jinja_env.get_template(template_name)
    return template.render(**context)


def exige_login(perfil_minimo=None):
    """
    perfil_minimo: None | 'consulta' | 'operador' | 'admin'
    Hierarquia: consulta < operador < admin
    """
    user = usuario_atual()
    if not user:
        return redirect("/login")
    if perfil_minimo:
        ordem = {"consulta": 1, "operador": 2, "admin": 3}
        if ordem.get(user.get("perfil"), 0) < ordem.get(perfil_minimo, 99):
            return HTTPError(403, "Acesso negado para o seu perfil.")
    return None


@app.hook("before_request")
def _proteger_rotas():
    path = request.path or "/"
    if path.startswith("/static"):
        return
    if path in ("/login",):
        return
    user = usuario_atual()
    if not user:
        # permite só login
        if path != "/login":
            return redirect("/login")
    # Perfil consulta: bloqueia métodos de escrita
    if user and user.get("perfil") == "consulta" and request.method in ("POST", "PUT", "DELETE"):
        if not path.startswith("/login"):
            return HTTPError(403, "Perfil consulta: apenas leitura.")



def form_to_dict(keys):
    data = {}
    for k in keys:
        val = request.forms.get(k, "").strip()
        data[k] = val if val else None
    return data


def salvar_upload(campo_nome, prefixo="doc"):
    """
    Salva arquivo enviado no formulário.
    Retorna caminho relativo (static/uploads/...) ou None se não houver arquivo.
    """
    upload = request.files.get(campo_nome)
    if not upload or not getattr(upload, "filename", None):
        return None
    nome_original = upload.filename
    # sanitiza extensão
    ext = os.path.splitext(nome_original)[1].lower()
    if ext not in (".jpg", ".jpeg", ".png", ".gif", ".webp", ".pdf", ".bmp"):
        ext = ".jpg"
    import uuid
    nome_seguro = "%s_%s%s" % (prefixo, uuid.uuid4().hex[:12], ext)
    pasta = os.path.join(BASE_DIR, "static", "uploads")
    os.makedirs(pasta, exist_ok=True)
    caminho_abs = os.path.join(pasta, nome_seguro)
    upload.save(caminho_abs)
    return "static/uploads/" + nome_seguro


# ========== STATIC ==========
@app.route("/static/<filepath:path>")
def serve_static(filepath):
    return static_file(filepath, root=STATIC_DIR)


# ========== APIs CEP / CNPJ ==========
@app.route("/api/cep/<cep>")
def api_cep(cep):
    """Consulta endereço pelo CEP (ViaCEP)."""
    import json
    import urllib.request
    import urllib.error
    response.content_type = "application/json; charset=utf-8"
    digitos = "".join(c for c in (cep or "") if c.isdigit())
    if len(digitos) != 8:
        return json.dumps({"ok": False, "erro": "CEP deve ter 8 dígitos."})
    url = "https://viacep.com.br/ws/%s/json/" % digitos
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "ControleContratos/1.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        if data.get("erro"):
            return json.dumps({"ok": False, "erro": "CEP não encontrado."})
        return json.dumps({
            "ok": True,
            "cep": data.get("cep") or digitos,
            "logradouro": data.get("logradouro") or "",
            "bairro": data.get("bairro") or "",
            "cidade": data.get("localidade") or "",
            "uf": data.get("uf") or "",
        }, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"ok": False, "erro": "Falha ao consultar CEP: %s" % str(e)})


@app.route("/api/cnpj/<cnpj>")
def api_cnpj(cnpj):
    """Consulta dados da empresa pelo CNPJ (BrasilAPI)."""
    import json
    import urllib.request
    import urllib.error
    response.content_type = "application/json; charset=utf-8"
    digitos = "".join(c for c in (cnpj or "") if c.isdigit())
    if len(digitos) != 14:
        return json.dumps({"ok": False, "erro": "CNPJ deve ter 14 dígitos."})
    url = "https://brasilapi.com.br/api/cnpj/v1/%s" % digitos
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "ControleContratos/1.0"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        # Formata CNPJ
        fmt = "%s.%s.%s/%s-%s" % (
            digitos[0:2], digitos[2:5], digitos[5:8], digitos[8:12], digitos[12:14]
        )
        cep = (data.get("cep") or "").replace(".", "").replace("-", "")
        if len(cep) == 8:
            cep_fmt = "%s-%s" % (cep[:5], cep[5:])
        else:
            cep_fmt = data.get("cep") or ""
        return json.dumps({
            "ok": True,
            "documento": fmt,
            "nome": data.get("razao_social") or data.get("nome_fantasia") or "",
            "nome_fantasia": data.get("nome_fantasia") or "",
            "email": data.get("email") or "",
            "telefone": data.get("ddd_telefone_1") or "",
            "cep": cep_fmt,
            "logradouro": (("" if not data.get("descricao_tipo_de_logradouro") else data.get("descricao_tipo_de_logradouro") + " ") + (data.get("logradouro") or "")).strip(),
            "numero": data.get("numero") or "",
            "bairro": data.get("bairro") or "",
            "cidade": data.get("municipio") or "",
            "uf": data.get("uf") or "",
        }, ensure_ascii=False)
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return json.dumps({"ok": False, "erro": "CNPJ não encontrado."})
        return json.dumps({"ok": False, "erro": "Erro na consulta CNPJ (HTTP %s)." % e.code})
    except Exception as e:
        return json.dumps({"ok": False, "erro": "Falha ao consultar CNPJ: %s" % str(e)})




# ========== DASHBOARD ==========
@app.route("/")
def index():
    from datetime import date
    cid = escopo_contratante_id()
    sid = escopo_setor_id()
    stats = db.dashboard_stats(contratante_id=cid, setor_id=sid)
    contratos = db.consultar_contratos(contratante_id=cid, setor_id=sid)
    vencendo_30 = db.consultar_contratos(status="Ativo", vencimento_preset="30", contratante_id=cid, setor_id=sid)
    return render(
        "index.html",
        stats=stats,
        contratos=contratos,
        vencendo_30=vencendo_30,
        hoje=date.today().isoformat(),
    )


# ========== CONTRATANTES ==========
@app.route("/contratantes")
def list_contratantes():
    q = request.query.get("q", "").strip() or None
    cid = escopo_contratante_id()
    items = db.list_contratantes(search=q)
    if cid:
        items = [i for i in items if i["id"] == int(cid)]
    return render(
        "list_pessoa.html",
        titulo="Contratantes",
        items=items,
        base_url="/contratantes",
        search=q or "",
    )


@app.route("/contratantes/novo", method=["GET", "POST"])
def novo_contratante():
    if escopo_contratante_id():
        raise HTTPError(403, "Somente administrador pode cadastrar contratantes.")
    if request.method == "POST":
        data = form_to_dict([
            "nome", "cep", "logradouro", "numero", "bairro", "cidade", "uf",
            "documento", "email", "celular", "whatsapp",
        ])
        if not data["nome"]:
            return render(
                "form_pessoa.html",
                titulo="Novo Contratante",
                item=None,
                base_url="/contratantes",
                action="/contratantes/novo",
                message="Nome é obrigatório.",
                message_type="error",
            )
        db.save_contratante(data)
        return redirect("/contratantes")
    return render(
        "form_pessoa.html",
        titulo="Novo Contratante",
        item=None,
        base_url="/contratantes",
        action="/contratantes/novo",
    )


@app.route("/contratantes/<id:int>/editar", method=["GET", "POST"])
def editar_contratante(id):
    item = db.get_contratante(id)
    if not item:
        raise HTTPError(404, "Contratante não encontrado")
    cid = escopo_contratante_id()
    if cid and int(item["id"]) != int(cid):
        raise HTTPError(403, "Acesso negado a este contratante.")
    # Operador só visualiza; alteração só admin
    if request.method == "POST":
        if cid:
            raise HTTPError(403, "Somente administrador pode alterar contratantes.")
        data = form_to_dict([
            "nome", "cep", "logradouro", "numero", "bairro", "cidade", "uf",
            "documento", "email", "celular", "whatsapp",
        ])
        db.save_contratante(data, id=id)
        return redirect("/contratantes")
    return render(
        "form_pessoa.html",
        titulo="Editar Contratante",
        item=item,
        base_url="/contratantes",
        action="/contratantes/%d/editar" % id,
    )


@app.route("/contratantes/<id:int>/excluir", method="POST")
def excluir_contratante(id):
    if escopo_contratante_id():
        raise HTTPError(403, "Somente administrador pode excluir contratantes.")
    db.delete_contratante(id)
    return redirect("/contratantes")


# ========== CONTRATADOS ==========
@app.route("/contratados")
def list_contratados():
    q = request.query.get("q", "").strip() or None
    cid = escopo_contratante_id()
    items = db.list_contratados(search=q, contratante_id=cid)
    return render(
        "list_pessoa.html",
        titulo="Contratados",
        items=items,
        base_url="/contratados",
        search=q or "",
    )


@app.route("/contratados/novo", method=["GET", "POST"])
def novo_contratado():
    if request.method == "POST":
        data = form_to_dict([
            "nome", "cep", "logradouro", "numero", "bairro", "cidade", "uf",
            "documento", "email", "celular", "whatsapp",
        ])
        if not data["nome"]:
            return render(
                "form_pessoa.html",
                titulo="Novo Contratado",
                item=None,
                base_url="/contratados",
                action="/contratados/novo",
                com_fotos=True,
                message="Nome é obrigatório.",
                message_type="error",
            )
        # Fotos do documento pessoal e comprovante de residência
        foto_doc = salvar_upload("foto_documento", "doc_pessoal")
        foto_comp = salvar_upload("foto_comprovante", "comp_residencia")
        if foto_doc:
            data["foto_documento"] = foto_doc
        if foto_comp:
            data["foto_comprovante"] = foto_comp
        data = forcar_contratante_no_data(data)
        db.save_contratado(data)
        return redirect("/contratados")
    return render(
        "form_pessoa.html",
        titulo="Novo Contratado",
        item=None,
        base_url="/contratados",
        action="/contratados/novo",
        com_fotos=True,
    )


@app.route("/contratados/<id:int>/editar", method=["GET", "POST"])
def editar_contratado(id):
    item = db.get_contratado(id)
    if not item:
        raise HTTPError(404, "Contratado não encontrado")
    cid = escopo_contratante_id()
    if cid and item.get("contratante_id") and int(item["contratante_id"]) != int(cid):
        raise HTTPError(403, "Acesso negado a este contratado.")
    if request.method == "POST":
        data = form_to_dict([
            "nome", "cep", "logradouro", "numero", "bairro", "cidade", "uf",
            "documento", "email", "celular", "whatsapp",
        ])
        foto_doc = salvar_upload("foto_documento", "doc_pessoal")
        foto_comp = salvar_upload("foto_comprovante", "comp_residencia")
        if foto_doc:
            data["foto_documento"] = foto_doc
        if foto_comp:
            data["foto_comprovante"] = foto_comp
        data = forcar_contratante_no_data(data)
        cid = escopo_contratante_id()
        if cid and item.get("contratante_id") and int(item["contratante_id"]) != int(cid):
            raise HTTPError(403, "Acesso negado a este contratado.")
        db.save_contratado(data, id=id)
        return redirect("/contratados")
    return render(
        "form_pessoa.html",
        titulo="Editar Contratado",
        item=item,
        base_url="/contratados",
        action="/contratados/%d/editar" % id,
        com_fotos=True,
    )


@app.route("/contratados/<id:int>/excluir", method="POST")
def excluir_contratado(id):
    item = db.get_contratado(id)
    cid = escopo_contratante_id()
    if cid and item and item.get("contratante_id") and int(item["contratante_id"]) != int(cid):
        raise HTTPError(403, "Acesso negado a este contratado.")
    db.delete_contratado(id)
    return redirect("/contratados")


# ========== SETORES ==========
@app.route("/setores")
def list_setores():
    cid = escopo_contratante_id()
    itens = db.list_setores(contratante_id=cid)
    return render("list_setores.html", itens=itens)


@app.route("/setores/novo", method=["GET", "POST"])
def novo_setor():
    cid = escopo_contratante_id()
    if cid:
        contratantes = [c for c in db.list_contratantes() if c["id"] == int(cid)]
    else:
        contratantes = db.list_contratantes()
    if request.method == "POST":
        data = form_to_dict(["nome", "responsavel", "nrcelular", "contratante_id"])
        data = forcar_contratante_no_data(data)
        if not data.get("nome"):
            return render(
                "form_setor.html",
                titulo="Novo Setor",
                item=None,
                action="/setores/novo",
                contratantes=contratantes,
                message="Nome é obrigatório.",
                message_type="error",
            )
        if not data.get("contratante_id"):
            return render(
                "form_setor.html",
                titulo="Novo Setor",
                item=data,
                action="/setores/novo",
                contratantes=contratantes,
                message="Selecione o contratante do setor.",
                message_type="error",
            )
        db.save_setor(data)
        return redirect("/setores")
    return render(
        "form_setor.html",
        titulo="Novo Setor",
        item=None,
        action="/setores/novo",
        contratantes=contratantes,
    )


@app.route("/setores/<id:int>/editar", method=["GET", "POST"])
def editar_setor(id):
    item = db.get_setor(id)
    if not item:
        raise HTTPError(404, "Setor não encontrado")
    cid = escopo_contratante_id()
    if cid and item.get("contratante_id") and int(item["contratante_id"]) != int(cid):
        raise HTTPError(403, "Acesso negado a este setor.")
    if cid:
        contratantes = [c for c in db.list_contratantes() if c["id"] == int(cid)]
    else:
        contratantes = db.list_contratantes()
    if request.method == "POST":
        data = form_to_dict(["nome", "responsavel", "nrcelular", "contratante_id"])
        data = forcar_contratante_no_data(data)
        if not data.get("contratante_id"):
            return render(
                "form_setor.html",
                titulo="Editar Setor",
                item=item,
                action="/setores/%d/editar" % id,
                contratantes=contratantes,
                message="Selecione o contratante do setor.",
                message_type="error",
            )
        db.save_setor(data, id=id)
        return redirect("/setores")
    return render(
        "form_setor.html",
        titulo="Editar Setor",
        item=item,
        action="/setores/%d/editar" % id,
        contratantes=contratantes,
    )


@app.route("/setores/<id:int>/excluir", method="POST")
def excluir_setor(id):
    item = db.get_setor(id)
    cid = escopo_contratante_id()
    if cid and item and item.get("contratante_id") and int(item["contratante_id"]) != int(cid):
        raise HTTPError(403, "Acesso negado a este setor.")
    db.delete_setor(id)
    return redirect("/setores")


# ========== CONSULTAS ==========
def _filtros_consulta_da_request():
    """Lê filtros de consulta da query string."""
    status = request.query.get("status", "").strip() or None
    setor_id = request.query.get("setor_id", "").strip() or None
    vencimento_de = request.query.get("vencimento_de", "").strip() or None
    vencimento_ate = request.query.get("vencimento_ate", "").strip() or None
    vencimento_preset = request.query.get("vencimento_preset", "").strip() or None
    return {
        "status": status,
        "setor_id": setor_id,
        "vencimento_de": vencimento_de,
        "vencimento_ate": vencimento_ate,
        "vencimento_preset": vencimento_preset,
    }


def _query_string_filtros(filtros):
    """Monta query string a partir dos filtros (para link do PDF)."""
    from urllib.parse import urlencode
    params = {k: v for k, v in filtros.items() if v}
    return urlencode(params)


@app.route("/consultas")
def consultas():
    filtros = _filtros_consulta_da_request()
    cid = escopo_contratante_id()
    sid = escopo_setor_id()
    # Operador: setor fixo do vínculo; admin pode filtrar na tela
    setor_filtro = sid if sid else filtros["setor_id"]
    itens = db.consultar_contratos(
        status=filtros["status"],
        setor_id=setor_filtro,
        vencimento_de=filtros["vencimento_de"],
        vencimento_ate=filtros["vencimento_ate"],
        vencimento_preset=filtros["vencimento_preset"],
        contratante_id=cid,
    )
    setores = db.list_setores(contratante_id=cid)
    from datetime import date
    return render(
        "consultas.html",
        itens=itens,
        setores=setores,
        filtros=filtros,
        query_string=_query_string_filtros(filtros),
        hoje=date.today().isoformat(),
    )


@app.route("/consultas/pdf")
def consultas_pdf():
    filtros = _filtros_consulta_da_request()
    cid = escopo_contratante_id()
    sid = escopo_setor_id()
    # Operador: setor fixo do vínculo; admin pode filtrar na tela
    setor_filtro = sid if sid else filtros["setor_id"]
    itens = db.consultar_contratos(
        status=filtros["status"],
        setor_id=setor_filtro,
        vencimento_de=filtros["vencimento_de"],
        vencimento_ate=filtros["vencimento_ate"],
        vencimento_preset=filtros["vencimento_preset"],
        contratante_id=cid,
    )
    if not PDF_DISPONIVEL:
        detalhe = _PDF_ERRO or "desconhecido"
        return (
            "<html><body style='font-family:sans-serif;padding:2rem'>"
            "<h2>PDF indisponível</h2>"
            "<pre>%s</pre>"
            "<p><a href='/consultas'>Voltar</a></p></body></html>"
        ) % detalhe

    # Nome do setor para o cabeçalho do PDF
    setor_nome = None
    if filtros.get("setor_id"):
        s = db.get_setor(int(filtros["setor_id"]))
        if s:
            setor_nome = s.get("nome")
    filtros_pdf = dict(filtros)
    filtros_pdf["setor_nome"] = setor_nome

    try:
        pdf_path = gerar_pdf_consulta(itens, filtros=filtros_pdf)
        return static_file(
            os.path.basename(pdf_path),
            root=os.path.dirname(pdf_path),
            download="Consulta_Contratos.pdf",
        )
    except Exception as e:
        return (
            "<html><body style='font-family:sans-serif;padding:2rem'>"
            "<h2>Erro ao gerar PDF</h2><pre>%s</pre>"
            "<p><a href='/consultas'>Voltar</a></p></body></html>"
        ) % str(e)


# ========== CONTRATOS ==========
@app.route("/contratos")
def list_contratos():
    from datetime import date
    status = request.query.get("status", "").strip() or None
    cid = escopo_contratante_id()
    sid = escopo_setor_id()
    itens = db.consultar_contratos(status=status, contratante_id=cid, setor_id=sid)
    return render(
        "list_contratos.html",
        itens=itens,
        status_filter=status or "",
        hoje=date.today().isoformat(),
    )


def _listas_para_contrato():
    """Listas de contratante/contratado/setor respeitando o escopo do usuário."""
    cid = escopo_contratante_id()
    sid = escopo_setor_id()
    if cid:
        todos_ct = db.list_contratantes()
        contratantes = [c for c in todos_ct if c["id"] == int(cid)]
        contratados = db.list_contratados(contratante_id=cid)
        setores = db.list_setores(contratante_id=cid)
    else:
        contratantes = db.list_contratantes()
        contratados = db.list_contratados()
        setores = db.list_setores()
    if sid:
        setores = [s for s in setores if s["id"] == int(sid)]
    return contratantes, contratados, setores


def _garantir_acesso_contrato(c):
    cid = escopo_contratante_id()
    sid = escopo_setor_id()
    if cid and c and int(c.get("contratante_id") or 0) != int(cid):
        raise HTTPError(403, "Acesso negado a este contrato (contratante).")
    if sid and c and c.get("setor_id") and int(c.get("setor_id") or 0) != int(sid):
        raise HTTPError(403, "Acesso negado a este contrato (setor).")


@app.route("/contratos/novo", method=["GET", "POST"])
def novo_contrato():
    contratantes, contratados, setores = _listas_para_contrato()
    if request.method == "POST":
        data = form_to_dict([
            "numero", "contratante_id", "contratado_id", "setor_id",
            "objeto", "valor", "data_inicio", "data_fim", "status", "observacoes",
        ])
        data["contratante_id"] = int(data["contratante_id"]) if data.get("contratante_id") else None
        data["contratado_id"] = int(data["contratado_id"]) if data.get("contratado_id") else None
        data["setor_id"] = int(data["setor_id"]) if data.get("setor_id") else None
        data = forcar_vinculos_no_data(data)
        try:
            data["valor"] = float(data["valor"]) if data.get("valor") else 0
        except ValueError:
            data["valor"] = 0

        if not data.get("numero") or not data.get("contratante_id") or not data.get("contratado_id") or not data.get("objeto"):
            return render(
                "form_contrato.html",
                titulo="Novo Contrato",
                item=None,
                action="/contratos/novo",
                contratantes=contratantes,
                contratados=contratados,
                setores=setores,
                numero_sugerido=db.next_numero_contrato(),
                message="Preencha os campos obrigatórios.",
                message_type="error",
            )
        db.save_contrato(data)
        return redirect("/contratos")

    return render(
        "form_contrato.html",
        titulo="Novo Contrato",
        item=None,
        action="/contratos/novo",
        contratantes=contratantes,
        contratados=contratados,
        setores=setores,
        numero_sugerido=db.next_numero_contrato(),
    )


@app.route("/contratos/<id:int>")
def ver_contrato(id):
    c = db.get_contrato(id)
    if not c:
        raise HTTPError(404, "Contrato não encontrado")
    _garantir_acesso_contrato(c)
    return render("ver_contrato.html", c=c)


@app.route("/contratos/<id:int>/editar", method=["GET", "POST"])
def editar_contrato(id):
    item = db.get_contrato(id)
    if not item:
        raise HTTPError(404, "Contrato não encontrado")
    _garantir_acesso_contrato(item)
    contratantes, contratados, setores = _listas_para_contrato()
    if request.method == "POST":
        data = form_to_dict([
            "numero", "contratante_id", "contratado_id", "setor_id",
            "objeto", "valor", "data_inicio", "data_fim", "status", "observacoes",
        ])
        data["contratante_id"] = int(data["contratante_id"]) if data.get("contratante_id") else None
        data["contratado_id"] = int(data["contratado_id"]) if data.get("contratado_id") else None
        data["setor_id"] = int(data["setor_id"]) if data.get("setor_id") else None
        data = forcar_vinculos_no_data(data)
        try:
            data["valor"] = float(data["valor"]) if data.get("valor") else 0
        except ValueError:
            data["valor"] = 0
        db.save_contrato(data, id=id)
        return redirect("/contratos/%d" % id)

    return render(
        "form_contrato.html",
        titulo="Editar Contrato %s" % item["numero"],
        item=item,
        action="/contratos/%d/editar" % id,
        contratantes=contratantes,
        contratados=contratados,
        setores=setores,
        numero_sugerido=item["numero"],
    )


@app.route("/contratos/<id:int>/pdf")
def pdf_contrato(id):
    c = db.get_contrato(id)
    if not c:
        raise HTTPError(404, "Contrato não encontrado")
    _garantir_acesso_contrato(c)
    if not PDF_DISPONIVEL:
        detalhe = _PDF_ERRO or "desconhecido"
        return (
            "<html><body style='font-family:sans-serif;padding:2rem'>"
            "<h2>PDF indisponível</h2>"
            "<p>Faça o seguinte:</p>"
            "<ol>"
            "<li>No terminal, rode: <pre>pip install reportlab</pre></li>"
            "<li><b>Pare o servidor</b> (Ctrl+C no terminal)</li>"
            "<li>Inicie de novo: <pre>python app.py</pre></li>"
            "</ol>"
            "<p>Se já fez isso, o erro técnico foi:</p>"
            "<pre style='background:#fee;padding:1rem'>%s</pre>"
            "<p><a href='/contratos/%d'>Voltar</a></p>"
            "</body></html>"
        ) % (detalhe, id)
    try:
        pdf_path = gerar_pdf_contrato(c)
        return static_file(
            os.path.basename(pdf_path),
            root=os.path.dirname(pdf_path),
            download="Contrato_%s.pdf" % c["numero"],
        )
    except Exception as e:
        return (
            "<h2>Erro ao gerar PDF</h2>"
            "<pre>%s</pre>"
            "<p><a href='/contratos/%d'>Voltar</a></p>" % (str(e), id)
        )


@app.route("/contratos/<id:int>/excluir", method="POST")
def excluir_contrato(id):
    db.delete_contrato(id)
    return redirect("/contratos")



# ========== LOGIN / LOGOUT ==========
@app.route("/login", method=["GET", "POST"])
def login():
    if usuario_atual():
        return redirect("/")
    if request.method == "POST":
        login_val = (request.forms.get("login") or "").strip()
        senha = request.forms.get("senha") or ""
        user = db.autenticar(login_val, senha)
        if not user:
            return render(
                "login.html",
                message="Login ou senha inválidos.",
                message_type="error",
                usuario=None,
            )
        token = _criar_sessao(user)
        response.set_cookie(
            SESSION_COOKIE,
            token,
            path="/",
            httponly=True,
            max_age=SESSION_MAX_AGE,
            samesite="Lax",
        )
        return redirect("/")
    return render("login.html", usuario=None)


@app.route("/logout")
def logout():
    response.delete_cookie(SESSION_COOKIE, path="/")
    return redirect("/login")


# ========== USUÁRIOS (somente admin) ==========
@app.route("/usuarios")
def list_usuarios():
    neg = exige_login("admin")
    if neg:
        return neg
    return render("list_usuarios.html", itens=db.list_usuarios())


@app.route("/usuarios/novo", method=["GET", "POST"])
def novo_usuario():
    neg = exige_login("admin")
    if neg:
        return neg
    if request.method == "POST":
        data = form_to_dict(["nome", "login", "senha", "perfil", "ativo", "contratante_id", "setor_id"])
        if not data.get("nome") or not data.get("login") or not data.get("senha"):
            return render(
                "form_usuario.html",
                titulo="Novo Usuário",
                item=None,
                action="/usuarios/novo",
                contratantes=db.list_contratantes(),
                setores=db.list_setores(),
                message="Preencha nome, login e senha.",
                message_type="error",
            )
        if len(data["senha"]) < 6:
            return render(
                "form_usuario.html",
                titulo="Novo Usuário",
                item=None,
                action="/usuarios/novo",
                contratantes=db.list_contratantes(),
                setores=db.list_setores(),
                message="Senha deve ter no mínimo 6 caracteres.",
                message_type="error",
            )
        if db.get_usuario_por_login(data["login"]):
            return render(
                "form_usuario.html",
                titulo="Novo Usuário",
                item=data,
                action="/usuarios/novo",
                contratantes=db.list_contratantes(),
                setores=db.list_setores(),
                message="Este login já existe.",
                message_type="error",
            )
        if data.get("perfil") in ("operador", "consulta") and (not data.get("contratante_id") or not data.get("setor_id")):
            return render(
                "form_usuario.html",
                titulo="Novo Usuário",
                item=data,
                action="/usuarios/novo",
                contratantes=db.list_contratantes(),
                setores=db.list_setores(),
                message="Operador e consulta precisam de contratante e setor vinculados.",
                message_type="error",
            )
        db.save_usuario(data)
        return redirect("/usuarios")
    return render("form_usuario.html", titulo="Novo Usuário", item=None, action="/usuarios/novo", contratantes=db.list_contratantes(), setores=db.list_setores())


@app.route("/usuarios/<id:int>/editar", method=["GET", "POST"])
def editar_usuario(id):
    neg = exige_login("admin")
    if neg:
        return neg
    item = db.get_usuario(id)
    if not item:
        raise HTTPError(404, "Usuário não encontrado")
    if request.method == "POST":
        data = form_to_dict(["nome", "login", "senha", "perfil", "ativo", "contratante_id", "setor_id"])
        if not data.get("nome") or not data.get("login"):
            return render(
                "form_usuario.html",
                titulo="Editar Usuário",
                item=item,
                action="/usuarios/%d/editar" % id,
                contratantes=db.list_contratantes(),
                setores=db.list_setores(),
                message="Nome e login são obrigatórios.",
                message_type="error",
            )
        if data.get("senha") and len(data["senha"]) < 6:
            return render(
                "form_usuario.html",
                titulo="Editar Usuário",
                item=item,
                action="/usuarios/%d/editar" % id,
                contratantes=db.list_contratantes(),
                setores=db.list_setores(),
                message="Senha deve ter no mínimo 6 caracteres.",
                message_type="error",
            )
        outro = db.get_usuario_por_login(data["login"])
        if outro and outro["id"] != id:
            return render(
                "form_usuario.html",
                titulo="Editar Usuário",
                item=item,
                action="/usuarios/%d/editar" % id,
                contratantes=db.list_contratantes(),
                setores=db.list_setores(),
                message="Este login já existe.",
                message_type="error",
            )
        db.save_usuario(data, id=id)
        return redirect("/usuarios")
    return render(
        "form_usuario.html",
        titulo="Editar Usuário",
        item=item,
        action="/usuarios/%d/editar" % id,
        contratantes=db.list_contratantes(),
        setores=db.list_setores(),
    )


@app.route("/usuarios/<id:int>/excluir", method="POST")
def excluir_usuario(id):
    neg = exige_login("admin")
    if neg:
        return neg
    user = usuario_atual()
    if user and user["id"] == id:
        return render(
            "list_usuarios.html",
            itens=db.list_usuarios(),
            message="Você não pode excluir o próprio usuário.",
            message_type="error",
        )
    db.delete_usuario(id)
    return redirect("/usuarios")



# ========== MAIN ==========
if __name__ == "__main__":
    print()
    print("=" * 60)
    print("  SISTEMA DE CONTROLE DE CONTRATOS")
    print("=" * 60)
    print()
    print("  Inicializando banco de dados...")
    try:
        db.init_db()
        try:
            if db.carregar_seed_se_vazio():
                print("  Dados iniciais (seed) carregados.")
        except Exception as e:
            print("  Aviso seed:", e)
        criou_admin = db.ensure_admin_padrao()
        print("  Banco de dados pronto!")
        if criou_admin:
            print("  Usuário padrão criado: login=admin  senha=admin123")
            print("  (Altere essa senha após o primeiro acesso)")
    except Exception as e:
        print("  ERRO ao criar banco:", e)
        sys.exit(1)

    print()
    if PDF_DISPONIVEL:
        print("  PDF de contratos: disponível")
    else:
        print("  PDF de contratos: indisponível (pip install reportlab)")
    print()
    port = int(os.environ.get("PORT", "8080"))
    host = os.environ.get("HOST", "0.0.0.0")
    print("  --------------------------------------------------")
    print("  Segurança: login obrigatório")
    print("  Abra o navegador em:")
    print()
    print("      >>>  http://%s:%s  <<<" % (host if host != "0.0.0.0" else "127.0.0.1", port))
    print()
    print("  Pressione Ctrl+C para encerrar o servidor.")
    print("  --------------------------------------------------")
    print()

    # host 127.0.0.1 = só neste computador (mais seguro e evita bloqueio de firewall)
    try:
        port = int(os.environ.get("PORT", "8080"))
        host = os.environ.get("HOST", "0.0.0.0")
        bottle.run(app, host=host, port=port, debug=False, reloader=False)
    except OSError as e:
        if "Address already in use" in str(e) or "address already in use" in str(e).lower():
            print()
            print("  ERRO: a porta 8080 já está em uso.")
            print("  Feche o outro programa ou altere a porta no final do app.py")
            print()
        else:
            print("  ERRO ao iniciar servidor:", e)
        sys.exit(1)
