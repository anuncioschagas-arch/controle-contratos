#!/usr/bin/env python3
"""Persistencia: aviso + caminho SQLite; Postgres se DATABASE_URL."""
from pathlib import Path
import os
import shutil
import re
import sqlite3

RESOLVE = '''
def _resolve_data_dir():
    import os
    env_file = os.environ.get("DATABASE_PATH") or os.environ.get("DB_PATH")
    if env_file:
        parent = os.path.dirname(env_file) or "."
        os.makedirs(parent, exist_ok=True)
        return parent, env_file
    data_dir = os.environ.get("DATA_DIR")
    if not data_dir:
        data_dir = "/data" if os.path.isdir("/data") else os.path.dirname(os.path.abspath(__file__))
    os.makedirs(data_dir, exist_ok=True)
    return data_dir, os.path.join(data_dir, "contratos.db")

_DATA_DIR, DB_PATH = _resolve_data_dir()
UPLOAD_DIR = os.path.join(_DATA_DIR, "uploads")
_STATIC_UPLOAD = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static", "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(_STATIC_UPLOAD, exist_ok=True)
'''

PG_LAYER = '''
DATABASE_URL = os.environ.get("DATABASE_URL") or os.environ.get("POSTGRES_URL") or ""
USE_POSTGRES = DATABASE_URL.startswith("postgres")

class _PgCursor:
    def __init__(self, cur):
        self._cur = cur
        self.lastrowid = None
    def execute(self, sql, params=None):
        sql2 = sql.replace("?", "%s")
        sql_strip = sql2.strip().upper()
        if sql_strip.startswith("INSERT") and "RETURNING" not in sql_strip:
            sql2 = sql2.rstrip().rstrip(";") + " RETURNING id"
            self._cur.execute(sql2, params or ())
            row = self._cur.fetchone()
            if row is not None:
                self.lastrowid = row[0] if not isinstance(row, dict) else list(row.values())[0]
            return self
        self._cur.execute(sql2, params or ())
        return self
    def fetchone(self):
        return self._cur.fetchone()
    def fetchall(self):
        return self._cur.fetchall()
    def __getattr__(self, name):
        return getattr(self._cur, name)

class _PgConn:
    def __init__(self, conn):
        self._conn = conn
    def execute(self, sql, params=None):
        from psycopg2.extras import RealDictCursor
        cur = self._conn.cursor(cursor_factory=RealDictCursor)
        pgcur = _PgCursor(cur)
        pgcur.execute(sql, params)
        return pgcur
    def cursor(self):
        from psycopg2.extras import RealDictCursor
        return _PgCursor(self._conn.cursor(cursor_factory=RealDictCursor))
    def commit(self):
        self._conn.commit()
    def rollback(self):
        self._conn.rollback()
    def close(self):
        self._conn.close()

def get_connection():
    if USE_POSTGRES:
        import psycopg2
        raw = psycopg2.connect(DATABASE_URL, sslmode="require")
        return _PgConn(raw)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        conn.execute("PRAGMA foreign_keys = ON")
    except Exception:
        pass
    return conn
'''

dbp = Path("database.py")
if dbp.exists():
    t = dbp.read_text(encoding="utf-8")
    if "_resolve_data_dir" not in t:
        m = re.search(r"^DB_PATH\s*=.*\n(?:UPLOAD_DIR\s*=.*\n)?", t, re.M)
        if m:
            t = t[: m.start()] + RESOLVE + "\n" + t[m.end() :]
            print("resolve injected")
    if "USE_POSTGRES" not in t:
        # replace get_connection function
        start = t.find("def get_connection(")
        if start >= 0:
            rest = t[start + 4 :]
            m = re.search(r"\ndef ", rest)
            end = start + 4 + m.start() if m else len(t)
            t = t[:start] + PG_LAYER + "\n" + t[end + 1 :]
            print("postgres layer injected")
        if "import sqlite3" not in t:
            t = "import sqlite3\n" + t
        if "import os" not in t:
            t = "import os\n" + t
    # _coluna_existe for postgres
    if "information_schema.columns" not in t:
        t = t.replace(
            '''def _coluna_existe(cur, tabela, coluna):
    cur.execute("PRAGMA table_info(%s)" % tabela)
    cols = [r[1] for r in cur.fetchall()]
    return coluna in cols''',
            '''def _coluna_existe(cur, tabela, coluna):
    if USE_POSTGRES:
        cur.execute(
            "SELECT 1 FROM information_schema.columns WHERE table_name = ? AND column_name = ? LIMIT 1",
            (tabela.lower(), coluna.lower()),
        )
        return cur.fetchone() is not None
    cur.execute("PRAGMA table_info(%s)" % tabela)
    cols = [r[1] for r in cur.fetchall()]
    return coluna in cols''',
        )
        print("coluna_existe patched")
    # sql adapt for init
    if "_sql_adapt" not in t:
        t = t.replace(
            "def init_db():",
            '''def _sql_adapt(sql):
    if not USE_POSTGRES:
        return sql
    s = sql.replace("INTEGER PRIMARY KEY AUTOINCREMENT", "SERIAL PRIMARY KEY")
    s = s.replace("AUTOINCREMENT", "")
    return s

def init_db():''',
        )
        t = t.replace(
            "with db_session() as conn:\n        cur = conn.cursor()",
            '''with db_session() as conn:
        if USE_POSTGRES:
            _real = conn.execute
            def _pg_exec(sql, params=None):
                if isinstance(sql, str):
                    sql = _sql_adapt(sql)
                if params is None:
                    return _real(sql)
                return _real(sql, params)
            conn.execute = _pg_exec
        cur = conn.cursor()''',
            1,
        )
        print("sql_adapt for init")
    dbp.write_text(t, encoding="utf-8")

url = os.environ.get("DATABASE_URL") or os.environ.get("POSTGRES_URL") or ""
if url.startswith("postgres"):
    print("DATABASE_URL detectado — usando PostgreSQL (persistente)")
else:
    print("AVISO: sem DATABASE_URL e sem disco /data — dados podem sumir no redeploy (plano free Render)")
print("fix_db_persist done")
