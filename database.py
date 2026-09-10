#!/usr/bin/env python3
"""
Controle de Contratos - Camada de Banco de Dados (SQLite)
"""

import sqlite3
import os
import hashlib
import secrets
from datetime import datetime
from contextlib import contextmanager

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "contratos.db")
UPLOAD_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static", "uploads")


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


@contextmanager
def db_session():
    conn = get_connection()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def _coluna_existe(cur, tabela, coluna):
    cur.execute("PRAGMA table_info(%s)" % tabela)
    cols = [r[1] for r in cur.fetchall()]
    return coluna in cols


def init_db():
    os.makedirs(UPLOAD_DIR, exist_ok=True)

    with db_session() as conn:
        cur = conn.cursor()

        cur.execute("""
            CREATE TABLE IF NOT EXISTS contratante (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT NOT NULL,
                cep TEXT,
                logradouro TEXT,
                numero TEXT,
                bairro TEXT,
                cidade TEXT,
                uf TEXT,
                documento TEXT,
                email TEXT,
                celular TEXT,
                whatsapp TEXT,
                criado_em TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        cur.execute("""
            CREATE TABLE IF NOT EXISTS contratado (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT NOT NULL,
                cep TEXT,
                logradouro TEXT,
                numero TEXT,
                bairro TEXT,
                cidade TEXT,
                uf TEXT,
                documento TEXT,
                email TEXT,
                celular TEXT,
                whatsapp TEXT,
                foto_documento TEXT,
                foto_comprovante TEXT,
                criado_em TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Migração: adiciona colunas de foto se a tabela já existia sem elas
        if not _coluna_existe(cur, "contratado", "foto_documento"):
            cur.execute("ALTER TABLE contratado ADD COLUMN foto_documento TEXT")
        if not _coluna_existe(cur, "contratado", "foto_comprovante"):
            cur.execute("ALTER TABLE contratado ADD COLUMN foto_comprovante TEXT")

        cur.execute("""
            CREATE TABLE IF NOT EXISTS setor (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT NOT NULL,
                responsavel TEXT,
                nrcelular TEXT,
                criado_em TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        cur.execute("""
            CREATE TABLE IF NOT EXISTS contrato (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                numero TEXT UNIQUE NOT NULL,
                contratante_id INTEGER NOT NULL,
                contratado_id INTEGER NOT NULL,
                setor_id INTEGER,
                objeto TEXT NOT NULL,
                valor REAL DEFAULT 0,
                valor_mensal REAL DEFAULT 0,
                quantidade_meses INTEGER DEFAULT 0,
                data_inicio TEXT,
                data_fim TEXT,
                status TEXT DEFAULT 'Ativo',
                observacoes TEXT,
                criado_em TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (contratante_id) REFERENCES contratante(id),
                FOREIGN KEY (contratado_id) REFERENCES contratado(id),
                FOREIGN KEY (setor_id) REFERENCES setor(id)
            )
        """)

        # Migração: colunas de valor mensal e quantidade de meses
        if not _coluna_existe(cur, "contrato", "valor_mensal"):
            cur.execute("ALTER TABLE contrato ADD COLUMN valor_mensal REAL DEFAULT 0")
        if not _coluna_existe(cur, "contrato", "quantidade_meses"):
            cur.execute("ALTER TABLE contrato ADD COLUMN quantidade_meses INTEGER DEFAULT 0")


        cur.execute("""
            CREATE TABLE IF NOT EXISTS usuario (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT NOT NULL,
                login TEXT NOT NULL UNIQUE,
                senha_hash TEXT NOT NULL,
                perfil TEXT NOT NULL DEFAULT 'operador',
                ativo INTEGER NOT NULL DEFAULT 1,
                contratante_id INTEGER,
                setor_id INTEGER,
                criado_em TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (contratante_id) REFERENCES contratante(id),
                FOREIGN KEY (setor_id) REFERENCES setor(id)
            )
        """)


        if not _coluna_existe(cur, "usuario", "contratante_id"):
            cur.execute("ALTER TABLE usuario ADD COLUMN contratante_id INTEGER")
        if not _coluna_existe(cur, "usuario", "setor_id"):
            cur.execute("ALTER TABLE usuario ADD COLUMN setor_id INTEGER")
        if not _coluna_existe(cur, "setor", "contratante_id"):
            cur.execute("ALTER TABLE setor ADD COLUMN contratante_id INTEGER")
        if not _coluna_existe(cur, "contratado", "contratante_id"):
            cur.execute("ALTER TABLE contratado ADD COLUMN contratante_id INTEGER")

        # Dados iniciais de exemplo (apenas se vazio)
        cur.execute("SELECT COUNT(*) FROM setor")
        if cur.fetchone()[0] == 0:
            cur.execute(
                "INSERT INTO setor (nome, responsavel, nrcelular) VALUES (?, ?, ?)",
                ("Administrativo", "João Silva", "(11) 99999-0001")
            )
            cur.execute(
                "INSERT INTO setor (nome, responsavel, nrcelular) VALUES (?, ?, ?)",
                ("Comercial", "Maria Souza", "(11) 99999-0002")
            )
            cur.execute(
                "INSERT INTO setor (nome, responsavel, nrcelular) VALUES (?, ?, ?)",
                ("Operações", "Carlos Lima", "(11) 99999-0003")
            )


# ========== CÁLCULOS ==========
def calcular_quantidade_meses(data_inicio, data_fim):
    """
    Calcula a quantidade de meses entre data_inicio e data_fim.
    Conta meses completos + 1 se houver dias restantes. Mínimo 1 se as datas forem válidas.
    """
    if not data_inicio or not data_fim:
        return 0
    try:
        d1 = datetime.strptime(str(data_inicio)[:10], "%Y-%m-%d")
        d2 = datetime.strptime(str(data_fim)[:10], "%Y-%m-%d")
        if d2 < d1:
            return 0
        # Diferença em anos e meses
        meses = (d2.year - d1.year) * 12 + (d2.month - d1.month)
        # Se o dia final for maior ou igual ao inicial, ou se passou do mês, ajusta
        if d2.day > d1.day:
            meses += 1
        elif d2.day < d1.day:
            # ainda não completou o mês — se meses==0 e há algum dia de diferença, conta 1
            pass
        # Garante pelo menos 1 mês quando há intervalo válido
        if meses == 0 and d2 >= d1:
            meses = 1
        return max(meses, 1) if d2 >= d1 else 0
    except Exception:
        return 0


def calcular_valor_mensal(valor_total, quantidade_meses):
    """Calcula valor mensal = valor total / quantidade de meses."""
    try:
        valor = float(valor_total or 0)
        meses = int(quantidade_meses or 0)
        if meses <= 0:
            return 0.0
        return round(valor / meses, 2)
    except Exception:
        return 0.0


def aplicar_calculos_contrato(data):
    """
    Preenche quantidade_meses e valor_mensal com base em data_inicio, data_fim e valor.
    Altera o dicionário data in-place e retorna ele.
    """
    qtd = calcular_quantidade_meses(data.get("data_inicio"), data.get("data_fim"))
    data["quantidade_meses"] = qtd
    data["valor_mensal"] = calcular_valor_mensal(data.get("valor"), qtd)
    return data


# ========== CONTRATANTE ==========
def list_contratantes(search=None):
    with db_session() as conn:
        if search:
            rows = conn.execute(
                "SELECT * FROM contratante WHERE nome LIKE ? OR documento LIKE ? ORDER BY nome",
                (f"%{search}%", f"%{search}%")
            ).fetchall()
        else:
            rows = conn.execute("SELECT * FROM contratante ORDER BY nome").fetchall()
        return [dict(r) for r in rows]


def get_contratante(id):
    with db_session() as conn:
        row = conn.execute("SELECT * FROM contratante WHERE id = ?", (id,)).fetchone()
        return dict(row) if row else None


def save_contratante(data, id=None):
    with db_session() as conn:
        if id:
            conn.execute("""
                UPDATE contratante SET
                    nome=?, cep=?, logradouro=?, numero=?, bairro=?, cidade=?, uf=?,
                    documento=?, email=?, celular=?, whatsapp=?
                WHERE id=?
            """, (
                data["nome"], data.get("cep"), data.get("logradouro"), data.get("numero"),
                data.get("bairro"), data.get("cidade"), data.get("uf"),
                data.get("documento"), data.get("email"), data.get("celular"),
                data.get("whatsapp"), id
            ))
            return id
        else:
            cur = conn.execute("""
                INSERT INTO contratante
                    (nome, cep, logradouro, numero, bairro, cidade, uf, documento, email, celular, whatsapp)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                data["nome"], data.get("cep"), data.get("logradouro"), data.get("numero"),
                data.get("bairro"), data.get("cidade"), data.get("uf"),
                data.get("documento"), data.get("email"), data.get("celular"),
                data.get("whatsapp")
            ))
            return cur.lastrowid


def delete_contratante(id):
    with db_session() as conn:
        conn.execute("DELETE FROM contratante WHERE id = ?", (id,))


# ========== CONTRATADO ==========
def list_contratados(search=None, contratante_id=None):
    """
    Lista contratados.
    Se contratante_id for informado: inclui os vinculados diretamente
    E também os que aparecem em contratos desse contratante.
    """
    with db_session() as conn:
        where = []
        params = []
        if contratante_id:
            cid = int(contratante_id)
            where.append(
                "(contratante_id = ? OR id IN ("
                "SELECT contratado_id FROM contrato WHERE contratante_id = ? AND contratado_id IS NOT NULL"
                "))"
            )
            params.extend([cid, cid])
        if search:
            where.append("(nome LIKE ? OR documento LIKE ?)")
            params.extend(["%%%s%%" % search, "%%%s%%" % search])
        sql = "SELECT * FROM contratado"
        if where:
            sql += " WHERE " + " AND ".join(where)
        sql += " ORDER BY nome"
        rows = conn.execute(sql, params).fetchall()
        return [dict(r) for r in rows]


def count_contratados(contratante_id=None):
    """Quantidade de contratados (escopo por contratante, se informado)."""
    with db_session() as conn:
        if contratante_id:
            cid = int(contratante_id)
            row = conn.execute(
                """
                SELECT COUNT(*) AS qtd FROM contratado
                WHERE contratante_id = ?
                   OR id IN (
                        SELECT contratado_id FROM contrato
                        WHERE contratante_id = ? AND contratado_id IS NOT NULL
                   )
                """,
                (cid, cid),
            ).fetchone()
            return int(row[0] if row[0] is not None else 0)
        row = conn.execute("SELECT COUNT(*) FROM contratado").fetchone()
        return int(row[0] or 0)


def get_contratado(id):
    with db_session() as conn:
        row = conn.execute("SELECT * FROM contratado WHERE id = ?", (id,)).fetchone()
        return dict(row) if row else None


def save_contratado(data, id=None):
    with db_session() as conn:
        if id:
            # Mantém fotos antigas se não foram enviadas novas
            atual = conn.execute("SELECT foto_documento, foto_comprovante FROM contratado WHERE id=?", (id,)).fetchone()
            foto_doc = data.get("foto_documento") or (atual["foto_documento"] if atual else None)
            foto_comp = data.get("foto_comprovante") or (atual["foto_comprovante"] if atual else None)
            conn.execute("""
                UPDATE contratado SET
                    nome=?, cep=?, logradouro=?, numero=?, bairro=?, cidade=?, uf=?,
                    documento=?, email=?, celular=?, whatsapp=?,
                    foto_documento=?, foto_comprovante=?, contratante_id=?
                WHERE id=?
            """, (
                data["nome"], data.get("cep"), data.get("logradouro"), data.get("numero"),
                data.get("bairro"), data.get("cidade"), data.get("uf"),
                data.get("documento"), data.get("email"), data.get("celular"),
                data.get("whatsapp"), foto_doc, foto_comp, data.get("contratante_id"), id
            ))
            return id
        else:
            cur = conn.execute("""
                INSERT INTO contratado
                    (nome, cep, logradouro, numero, bairro, cidade, uf, documento, email, celular, whatsapp,
                     foto_documento, foto_comprovante, contratante_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                data["nome"], data.get("cep"), data.get("logradouro"), data.get("numero"),
                data.get("bairro"), data.get("cidade"), data.get("uf"),
                data.get("documento"), data.get("email"), data.get("celular"),
                data.get("whatsapp"), data.get("foto_documento"), data.get("foto_comprovante"),
                data.get("contratante_id")
            ))
            return cur.lastrowid


def delete_contratado(id):
    with db_session() as conn:
        row = conn.execute("SELECT foto_documento, foto_comprovante FROM contratado WHERE id=?", (id,)).fetchone()
        if row:
            for campo in ("foto_documento", "foto_comprovante"):
                caminho = row[campo]
                if caminho:
                    full = os.path.join(os.path.dirname(DB_PATH), caminho) if not os.path.isabs(caminho) else caminho
                    # caminhos salvos como static/uploads/...
                    full2 = os.path.join(os.path.dirname(DB_PATH), caminho)
                    for p in (full, full2, os.path.join(UPLOAD_DIR, os.path.basename(caminho or ""))):
                        if p and os.path.isfile(p):
                            try:
                                os.remove(p)
                            except Exception:
                                pass
        conn.execute("DELETE FROM contratado WHERE id = ?", (id,))


# ========== SETOR ==========
def list_setores(contratante_id=None):
    with db_session() as conn:
        sql = """
            SELECT s.*, ct.nome AS contratante_nome
            FROM setor s
            LEFT JOIN contratante ct ON s.contratante_id = ct.id
        """
        params = []
        if contratante_id:
            sql += " WHERE s.contratante_id = ?"
            params.append(int(contratante_id))
        sql += " ORDER BY s.nome"
        rows = conn.execute(sql, params).fetchall()
        return [dict(r) for r in rows]


def get_setor(id):
    with db_session() as conn:
        row = conn.execute("""
            SELECT s.*, ct.nome AS contratante_nome
            FROM setor s
            LEFT JOIN contratante ct ON s.contratante_id = ct.id
            WHERE s.id = ?
        """, (id,)).fetchone()
        return dict(row) if row else None


def save_setor(data, id=None):
    with db_session() as conn:
        contratante_id = data.get("contratante_id") or None
        if contratante_id:
            try:
                contratante_id = int(contratante_id)
            except (TypeError, ValueError):
                contratante_id = None
        if id:
            conn.execute(
                "UPDATE setor SET nome=?, responsavel=?, nrcelular=?, contratante_id=? WHERE id=?",
                (data["nome"], data.get("responsavel"), data.get("nrcelular"), contratante_id, id)
            )
            return id
        else:
            cur = conn.execute(
                "INSERT INTO setor (nome, responsavel, nrcelular, contratante_id) VALUES (?, ?, ?, ?)",
                (data["nome"], data.get("responsavel"), data.get("nrcelular"), contratante_id)
            )
            return cur.lastrowid


def delete_setor(id):
    with db_session() as conn:
        conn.execute("DELETE FROM setor WHERE id = ?", (id,))


# ========== CONTRATO ==========
def list_contratos(status=None):
    return consultar_contratos(status=status)


def consultar_contratos(status=None, setor_id=None, vencimento_de=None, vencimento_ate=None,
                        vencimento_preset=None, contratante_id=None):
    """
    Consulta contratos com filtros:
      - status: Ativo / Encerrado / Cancelado
      - setor_id: id do setor
      - vencimento_de / vencimento_ate: intervalo em data_fim (YYYY-MM-DD)
      - vencimento_preset: 'vencidos' | 'mes' | '30' | '60' | '90'
    """
    from datetime import date, timedelta

    hoje = date.today()
    params = []
    where = []

    # Presets de vencimento (sobrescrevem de/até se informados sem datas manuais)
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
               s.nome AS setor_nome
        FROM contrato c
        LEFT JOIN contratante ct ON c.contratante_id = ct.id
        LEFT JOIN contratado cd ON c.contratado_id = cd.id
        LEFT JOIN setor s ON c.setor_id = s.id
    """
    if where:
        sql += " WHERE " + " AND ".join(where)
    sql += " ORDER BY c.data_fim ASC, c.id DESC"

    with db_session() as conn:
        rows = conn.execute(sql, params).fetchall()
        return [dict(r) for r in rows]


def get_contrato(id):
    with db_session() as conn:
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
                   s.nome AS setor_nome, s.responsavel AS setor_responsavel
            FROM contrato c
            LEFT JOIN contratante ct ON c.contratante_id = ct.id
            LEFT JOIN contratado cd ON c.contratado_id = cd.id
            LEFT JOIN setor s ON c.setor_id = s.id
            WHERE c.id = ?
        """, (id,)).fetchone()
        return dict(row) if row else None


def save_contrato(data, id=None):
    # Sempre recalcula meses e valor mensal a partir das datas e do valor total
    data = aplicar_calculos_contrato(data)

    with db_session() as conn:
        if id:
            conn.execute("""
                UPDATE contrato SET
                    numero=?, contratante_id=?, contratado_id=?, setor_id=?,
                    objeto=?, valor=?, valor_mensal=?, quantidade_meses=?,
                    data_inicio=?, data_fim=?, status=?, observacoes=?
                WHERE id=?
            """, (
                data["numero"], data["contratante_id"], data["contratado_id"],
                data.get("setor_id") or None, data["objeto"], data.get("valor", 0),
                data.get("valor_mensal", 0), data.get("quantidade_meses", 0),
                data.get("data_inicio"), data.get("data_fim"), data.get("status", "Ativo"),
                data.get("observacoes"), id
            ))
            return id
        else:
            cur = conn.execute("""
                INSERT INTO contrato
                    (numero, contratante_id, contratado_id, setor_id, objeto, valor,
                     valor_mensal, quantidade_meses, data_inicio, data_fim, status, observacoes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                data["numero"], data["contratante_id"], data["contratado_id"],
                data.get("setor_id") or None, data["objeto"], data.get("valor", 0),
                data.get("valor_mensal", 0), data.get("quantidade_meses", 0),
                data.get("data_inicio"), data.get("data_fim"), data.get("status", "Ativo"),
                data.get("observacoes")
            ))
            return cur.lastrowid


def delete_contrato(id):
    with db_session() as conn:
        conn.execute("DELETE FROM contrato WHERE id = ?", (id,))


def next_numero_contrato():
    """Gera próximo número de contrato no formato CT-AAAA-XXXX"""
    ano = datetime.now().year
    with db_session() as conn:
        row = conn.execute(
            "SELECT COUNT(*) as total FROM contrato WHERE numero LIKE ?",
            (f"CT-{ano}-%",)
        ).fetchone()
        seq = (row["total"] or 0) + 1
        return f"CT-{ano}-{seq:04d}"


def dashboard_stats(contratante_id=None, setor_id=None):
    from datetime import date, timedelta
    hoje = date.today().isoformat()
    limite_30 = (date.today() + timedelta(days=30)).isoformat()
    with db_session() as conn:
        def qtd_soma(where_sql="", params=()):
            row = conn.execute(
                "SELECT COUNT(*) AS qtd, COALESCE(SUM(valor), 0) AS soma FROM contrato " + where_sql,
                params,
            ).fetchone()
            return int(row["qtd"] or 0), float(row["soma"] or 0)

        clauses = []
        params = []
        if contratante_id:
            clauses.append("contratante_id = ?")
            params.append(int(contratante_id))
        if setor_id:
            clauses.append("setor_id = ?")
            params.append(int(setor_id))
        base = (" WHERE " + " AND ".join(clauses)) if clauses else ""

        total_qtd, total_soma = qtd_soma(base, tuple(params))
        ativos_qtd, ativos_soma = qtd_soma(
            (base + (" AND " if clauses else " WHERE ") + "status='Ativo'"), tuple(params)
        )
        encerrados_qtd, encerrados_soma = qtd_soma(
            (base + (" AND " if clauses else " WHERE ") + "status='Encerrado'"), tuple(params)
        )
        cancelados_qtd, cancelados_soma = qtd_soma(
            (base + (" AND " if clauses else " WHERE ") + "status='Cancelado'"), tuple(params)
        )
        vencidos_qtd, vencidos_soma = qtd_soma(
            base + (" AND " if clauses else " WHERE ") + "data_fim IS NOT NULL AND data_fim < ? AND status='Ativo'",
            tuple(params) + (hoje,),
        )
        vencendo_30_qtd, vencendo_30_soma = qtd_soma(
            base + (" AND " if clauses else " WHERE ") + "data_fim IS NOT NULL AND data_fim >= ? AND data_fim <= ? AND status='Ativo'",
            tuple(params) + (hoje, limite_30),
        )

        if contratante_id:
            total_contratantes = 1
            cid = int(contratante_id)
            total_contratados = conn.execute(
                """
                SELECT COUNT(*) FROM contratado
                WHERE contratante_id = ?
                   OR id IN (
                        SELECT contratado_id FROM contrato
                        WHERE contratante_id = ? AND contratado_id IS NOT NULL
                   )
                """,
                (cid, cid),
            ).fetchone()[0]
        else:
            total_contratantes = conn.execute("SELECT COUNT(*) FROM contratante").fetchone()[0]
            total_contratados = conn.execute("SELECT COUNT(*) FROM contratado").fetchone()[0]

        return {
            "total_contratos": total_qtd,
            "total_soma": total_soma,
            "ativos": ativos_qtd,
            "ativos_soma": ativos_soma,
            "encerrados_qtd": encerrados_qtd,
            "encerrados_soma": encerrados_soma,
            "cancelados_qtd": cancelados_qtd,
            "cancelados_soma": cancelados_soma,
            "vencidos": vencidos_qtd,
            "vencidos_soma": vencidos_soma,
            "vencendo_30": vencendo_30_qtd,
            "vencendo_30_soma": vencendo_30_soma,
            "total_contratantes": total_contratantes,
            "total_contratados": total_contratados,
        }


def _hash_senha(senha, salt=None):
    """Gera hash PBKDF2 da senha. Retorna string salt$hash."""
    if salt is None:
        salt = secrets.token_hex(16)
    h = hashlib.pbkdf2_hmac("sha256", senha.encode("utf-8"), salt.encode("utf-8"), 120000)
    return "%s$%s" % (salt, h.hex())


def verificar_senha(senha, senha_hash):
    try:
        salt, _ = senha_hash.split("$", 1)
    except ValueError:
        return False
    return secrets.compare_digest(_hash_senha(senha, salt), senha_hash)


def list_usuarios():
    with db_session() as conn:
        rows = conn.execute(
            "SELECT u.id, u.nome, u.login, u.perfil, u.ativo, u.criado_em, u.contratante_id, u.setor_id, ct.nome AS contratante_nome, s.nome AS setor_nome FROM usuario u LEFT JOIN contratante ct ON u.contratante_id = ct.id LEFT JOIN setor s ON u.setor_id = s.id ORDER BY u.nome"
        ).fetchall()
        return [dict(r) for r in rows]


def get_usuario(id):
    with db_session() as conn:
        row = conn.execute(
            "SELECT u.id, u.nome, u.login, u.perfil, u.ativo, u.criado_em, u.contratante_id, u.setor_id, ct.nome AS contratante_nome, s.nome AS setor_nome FROM usuario u LEFT JOIN contratante ct ON u.contratante_id = ct.id LEFT JOIN setor s ON u.setor_id = s.id WHERE u.id=?",
            (id,),
        ).fetchone()
        return dict(row) if row else None


def get_usuario_por_login(login):
    with db_session() as conn:
        row = conn.execute(
            "SELECT * FROM usuario WHERE login=? COLLATE NOCASE",
            (login.strip(),),
        ).fetchone()
        return dict(row) if row else None


def autenticar(login, senha):
    user = get_usuario_por_login(login)
    if not user:
        return None
    if not user.get("ativo"):
        return None
    if not verificar_senha(senha, user["senha_hash"]):
        return None
    return {
        "id": user["id"],
        "nome": user["nome"],
        "login": user["login"],
        "perfil": user["perfil"],
        "contratante_id": user.get("contratante_id"),
        "setor_id": user.get("setor_id"),
    }


def save_usuario(data, id=None):
    with db_session() as conn:
        perfil = data.get("perfil") or "operador"
        if perfil not in ("admin", "operador", "consulta"):
            perfil = "operador"
        ativo = 1 if data.get("ativo", True) in (True, 1, "1", "on", "true") else 0
        contratante_id = data.get("contratante_id") or None
        if contratante_id:
            try:
                contratante_id = int(contratante_id)
            except (TypeError, ValueError):
                contratante_id = None
        setor_id = data.get("setor_id") or None
        if setor_id:
            try:
                setor_id = int(setor_id)
            except (TypeError, ValueError):
                setor_id = None
        # Admin não precisa de vínculo; operador/consulta devem ter contratante (e preferencialmente setor)
        if perfil == "admin":
            contratante_id = None
            setor_id = None
        if id:
            if data.get("senha"):
                senha_hash = _hash_senha(data["senha"])
                conn.execute(
                    "UPDATE usuario SET nome=?, login=?, senha_hash=?, perfil=?, ativo=?, contratante_id=?, setor_id=? WHERE id=?",
                    (data["nome"], data["login"].strip(), senha_hash, perfil, ativo, contratante_id, setor_id, id),
                )
            else:
                conn.execute(
                    "UPDATE usuario SET nome=?, login=?, perfil=?, ativo=?, contratante_id=?, setor_id=? WHERE id=?",
                    (data["nome"], data["login"].strip(), perfil, ativo, contratante_id, setor_id, id),
                )
            return id
        else:
            senha_hash = _hash_senha(data["senha"])
            cur = conn.execute(
                "INSERT INTO usuario (nome, login, senha_hash, perfil, ativo, contratante_id, setor_id) VALUES (?,?,?,?,?,?,?)",
                (data["nome"], data["login"].strip(), senha_hash, perfil, ativo, contratante_id, setor_id),
            )
            return cur.lastrowid


def delete_usuario(id):
    with db_session() as conn:
        conn.execute("DELETE FROM usuario WHERE id=?", (id,))



def carregar_seed_se_vazio():
    """Carrega seed_data.sql se o banco estiver sem contratos/usuários úteis."""
    seed_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "seed_data.sql")
    if not os.path.isfile(seed_path):
        return False
    with db_session() as conn:
        try:
            n_ct = conn.execute("SELECT COUNT(*) FROM contrato").fetchone()[0]
        except Exception:
            n_ct = 0
        try:
            n_user = conn.execute("SELECT COUNT(*) FROM usuario").fetchone()[0]
        except Exception:
            n_user = 0
        # Só importa se banco praticamente vazio de negócio
        if n_ct > 0:
            return False
        with open(seed_path, "r", encoding="utf-8") as f:
            sql = f.read()
        conn.executescript(sql)
        return True


def ensure_admin_padrao():
    """Cria usuário admin/admin123 se não existir nenhum usuário."""
    with db_session() as conn:
        total = conn.execute("SELECT COUNT(*) FROM usuario").fetchone()[0]
        if total == 0:
            senha_hash = _hash_senha("admin123")
            conn.execute(
                "INSERT INTO usuario (nome, login, senha_hash, perfil, ativo) VALUES (?,?,?,?,?)",
                ("Administrador", "admin", senha_hash, "admin", 1),
            )
            return True
    return False
