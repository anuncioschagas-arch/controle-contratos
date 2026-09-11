#!/usr/bin/env python3
"""Instala chat (tabela, funcoes DB, rotas, CSS) no boot."""
from pathlib import Path
import re

css_path = Path("static/style.css")
if css_path.exists():
    css = css_path.read_text(encoding="utf-8")
    if ".chat-layout" not in css:
        css += """
.chat-layout { display: grid; grid-template-columns: 260px 1fr; gap: 1rem; min-height: 70vh; }
@media (max-width: 800px) { .chat-layout { grid-template-columns: 1fr; } }
.chat-sidebar { padding: 0.75rem; overflow-y: auto; max-height: 75vh; }
.chat-contact { display: block; padding: 0.6rem 0.7rem; border-radius: 8px; color: inherit; text-decoration: none; margin-bottom: 0.25rem; }
.chat-contact:hover { background: #edf2f7; text-decoration: none; }
.chat-contact.active { background: #ebf8ff; border: 1px solid #90cdf4; }
.chat-contact small { display: block; color: #718096; font-size: 0.75rem; }
.chat-preview { display: block; font-size: 0.75rem; color: #a0aec0; margin-top: 0.15rem; }
.chat-main { display: flex; flex-direction: column; padding: 0; overflow: hidden; max-height: 75vh; }
.chat-header { padding: 0.85rem 1rem; border-bottom: 1px solid #e2e8f0; background: rgba(247,250,252,0.95); }
.chat-messages { flex: 1; overflow-y: auto; padding: 1rem; display: flex; flex-direction: column; gap: 0.6rem; min-height: 320px; }
.chat-bubble { max-width: 75%; padding: 0.55rem 0.8rem; border-radius: 12px; font-size: 0.92rem; line-height: 1.4; }
.chat-bubble.mine { align-self: flex-end; background: #3182ce; color: #fff; border-bottom-right-radius: 4px; }
.chat-bubble.other { align-self: flex-start; background: #edf2f7; color: #1a202c; border-bottom-left-radius: 4px; }
.chat-meta { font-size: 0.72rem; font-weight: 600; margin-bottom: 0.2rem; opacity: 0.85; }
.chat-time { font-size: 0.68rem; opacity: 0.7; margin-top: 0.25rem; text-align: right; }
.chat-empty { color: #a0aec0; text-align: center; margin: 2rem 0; }
.chat-form { display: flex; gap: 0.5rem; padding: 0.75rem; border-top: 1px solid #e2e8f0; background: #fff; }
.chat-form input[type="text"] { flex: 1; padding: 0.55rem 0.75rem; border: 1px solid #e2e8f0; border-radius: 8px; font-size: 0.95rem; }
#chat-badge { display: none; background: #e53e3e; color: #fff; border-radius: 999px; font-size: 0.7rem; padding: 0.1rem 0.4rem; margin-left: 0.25rem; vertical-align: top; }
"""
        css_path.write_text(css, encoding="utf-8")
        print("chat css added")

dbp = Path("database.py")
if dbp.exists():
    t = dbp.read_text(encoding="utf-8")
    if "CREATE TABLE IF NOT EXISTS mensagem" not in t:
        insert = '''
        cur.execute("""
            CREATE TABLE IF NOT EXISTS mensagem (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                remetente_id INTEGER NOT NULL,
                destinatario_id INTEGER,
                texto TEXT NOT NULL,
                lida INTEGER DEFAULT 0,
                criado_em TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
'''
        if "CREATE TABLE IF NOT EXISTS setor" in t:
            p = t.find("CREATE TABLE IF NOT EXISTS setor")
            p2 = t.find('""")', p)
            p2 = t.find("\n", p2) + 1
            t = t[:p2] + insert + t[p2:]
            print("mensagem table in init_db")
    if "def enviar_mensagem" not in t:
        t = t.rstrip() + '''

def get_usuario(id):
    with db_session() as conn:
        row = conn.execute("SELECT * FROM usuario WHERE id = ?", (id,)).fetchone()
        return dict(row) if row else None

def list_usuarios_chat(exceto_id=None):
    with db_session() as conn:
        rows = conn.execute(
            "SELECT id, nome, login, perfil FROM usuario WHERE ativo = 1 AND perfil IN ('admin', 'operador') ORDER BY nome"
        ).fetchall()
        out = [dict(r) for r in rows]
        if exceto_id:
            out = [u for u in out if int(u["id"]) != int(exceto_id)]
        return out

def enviar_mensagem(remetente_id, texto, destinatario_id=None):
    texto = (texto or "").strip()
    if not texto:
        raise ValueError("Mensagem vazia")
    if len(texto) > 2000:
        texto = texto[:2000]
    with db_session() as conn:
        cur = conn.execute(
            "INSERT INTO mensagem (remetente_id, destinatario_id, texto, lida, criado_em) VALUES (?, ?, ?, 0, ?)",
            (int(remetente_id), int(destinatario_id) if destinatario_id else None, texto, datetime.now().isoformat(timespec="seconds")),
        )
        return cur.lastrowid

def list_mensagens(usuario_id, com_usuario_id=None, apos_id=0, limite=100):
    with db_session() as conn:
        if com_usuario_id:
            rows = conn.execute(
                """
                SELECT m.*, u.nome AS remetente_nome, u.perfil AS remetente_perfil
                FROM mensagem m JOIN usuario u ON u.id = m.remetente_id
                WHERE ((m.remetente_id = ? AND m.destinatario_id = ?) OR (m.remetente_id = ? AND m.destinatario_id = ?))
                AND m.id > ? ORDER BY m.id ASC LIMIT ?
                """,
                (int(usuario_id), int(com_usuario_id), int(com_usuario_id), int(usuario_id), int(apos_id or 0), int(limite)),
            ).fetchall()
        else:
            rows = conn.execute(
                """
                SELECT m.*, u.nome AS remetente_nome, u.perfil AS remetente_perfil
                FROM mensagem m JOIN usuario u ON u.id = m.remetente_id
                WHERE m.destinatario_id IS NULL AND m.id > ?
                ORDER BY m.id ASC LIMIT ?
                """,
                (int(apos_id or 0), int(limite)),
            ).fetchall()
        return [dict(r) for r in rows]

def marcar_mensagens_lidas(usuario_id, com_usuario_id=None):
    if not com_usuario_id:
        return
    with db_session() as conn:
        conn.execute(
            "UPDATE mensagem SET lida = 1 WHERE destinatario_id = ? AND remetente_id = ? AND lida = 0",
            (int(usuario_id), int(com_usuario_id)),
        )

def contar_nao_lidas(usuario_id):
    with db_session() as conn:
        row = conn.execute(
            "SELECT COUNT(*) FROM mensagem WHERE destinatario_id = ? AND lida = 0",
            (int(usuario_id),),
        ).fetchone()
        return int(row[0] or 0)

def resumo_conversas(usuario_id):
    with db_session() as conn:
        users = conn.execute(
            "SELECT id, nome, login, perfil FROM usuario WHERE ativo = 1 AND perfil IN ('admin', 'operador') AND id != ? ORDER BY nome",
            (int(usuario_id),),
        ).fetchall()
        out = []
        for u in users:
            uid = u["id"]
            last = conn.execute(
                """
                SELECT texto, criado_em, remetente_id FROM mensagem
                WHERE (remetente_id = ? AND destinatario_id = ?) OR (remetente_id = ? AND destinatario_id = ?)
                ORDER BY id DESC LIMIT 1
                """,
                (int(usuario_id), uid, uid, int(usuario_id)),
            ).fetchone()
            n = conn.execute(
                "SELECT COUNT(*) FROM mensagem WHERE destinatario_id = ? AND remetente_id = ? AND lida = 0",
                (int(usuario_id), uid),
            ).fetchone()[0]
            out.append({"id": uid, "nome": u["nome"], "login": u["login"], "perfil": u["perfil"],
                        "ultima": dict(last) if last else None, "nao_lidas": int(n or 0)})
        return out
'''
        print("chat db functions added")
    dbp.write_text(t, encoding="utf-8")

app = Path("app.py")
if app.exists():
    t = app.read_text(encoding="utf-8")
    if "def chat_page" not in t:
        routes = r'''

@app.route("/chat")
@app.route("/chat/com/<uid:int>")
def chat_page(uid=None):
    neg = exige_login("operador")
    if neg:
        return neg
    user = usuario_atual()
    if user.get("perfil") not in ("admin", "operador"):
        raise HTTPError(403, "Chat disponivel apenas para admin e operador.")
    com_usuario = None
    if uid:
        com_usuario = db.get_usuario(uid) if hasattr(db, "get_usuario") else None
        if not com_usuario:
            for u in db.list_usuarios_chat():
                if int(u["id"]) == int(uid):
                    com_usuario = u
                    break
        if not com_usuario:
            raise HTTPError(404, "Usuario nao encontrado")
        db.marcar_mensagens_lidas(user["id"], com_usuario["id"])
        mensagens = db.list_mensagens(user["id"], com_usuario_id=com_usuario["id"])
    else:
        mensagens = db.list_mensagens(user["id"], com_usuario_id=None)
    contatos = db.resumo_conversas(user["id"])
    return render("chat.html", mensagens=mensagens, contatos=contatos, com_usuario=com_usuario)

@app.route("/chat/enviar", method="POST")
def chat_enviar():
    import json
    response.content_type = "application/json; charset=utf-8"
    neg = exige_login("operador")
    if neg:
        return json.dumps({"ok": False, "erro": "login"})
    user = usuario_atual()
    if user.get("perfil") not in ("admin", "operador"):
        return json.dumps({"ok": False, "erro": "Sem permissao"})
    texto = (request.forms.get("texto") or "").strip()
    dest = request.forms.get("destinatario_id") or None
    if dest:
        try:
            dest = int(dest)
        except ValueError:
            dest = None
    try:
        mid = db.enviar_mensagem(user["id"], texto, dest)
    except ValueError as e:
        return json.dumps({"ok": False, "erro": str(e)})
    msgs = db.list_mensagens(user["id"], com_usuario_id=dest, apos_id=max(mid - 1, 0), limite=5)
    msg = None
    for m in msgs:
        if m["id"] == mid:
            msg = m
            break
    if not msg:
        msg = {"id": mid, "texto": texto, "remetente_id": user["id"], "remetente_nome": user.get("nome"), "remetente_perfil": user.get("perfil"), "criado_em": ""}
    return json.dumps({"ok": True, "mensagem": msg})

@app.route("/chat/api/mensagens")
def chat_api_mensagens():
    import json
    response.content_type = "application/json; charset=utf-8"
    neg = exige_login("operador")
    if neg:
        return json.dumps({"ok": False})
    user = usuario_atual()
    if user.get("perfil") not in ("admin", "operador"):
        return json.dumps({"ok": False})
    try:
        apos = int(request.query.get("apos") or 0)
    except ValueError:
        apos = 0
    com = request.query.get("com") or None
    if com:
        try:
            com = int(com)
            db.marcar_mensagens_lidas(user["id"], com)
        except ValueError:
            com = None
    return json.dumps({
        "ok": True,
        "mensagens": db.list_mensagens(user["id"], com_usuario_id=com, apos_id=apos),
        "nao_lidas": db.contar_nao_lidas(user["id"]),
    })
'''
        if "if __name__" in t:
            t = t.replace("if __name__", routes + "\nif __name__", 1)
        else:
            t = t.rstrip() + "\n" + routes
        print("chat routes added")
    if "contar_nao_lidas" not in t[t.find("def render"):t.find("def render")+500]:
        t2 = t.replace(
            'context.setdefault("usuario", usuario_atual())',
            'user = usuario_atual()\n    context.setdefault("usuario", user)\n    if "nao_lidas" not in context and user and user.get("perfil") in ("admin", "operador"):\n        try:\n            context["nao_lidas"] = db.contar_nao_lidas(user["id"])\n        except Exception:\n            context["nao_lidas"] = 0',
            1,
        )
        if t2 != t:
            t = t2
            print("render badge hooked")
    app.write_text(t, encoding="utf-8")
print("chat_install done")
