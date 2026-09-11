#!/usr/bin/env python3
"""Garante caminho persistente do SQLite e nao sobrescreve dados existentes."""
from pathlib import Path
import os
import shutil
import re
import sqlite3

RESOLVE = '''
def _resolve_data_dir():
    """Persistencia: DATABASE_PATH/DB_PATH ou DATA_DIR ou /data."""
    import os
    env_file = os.environ.get("DATABASE_PATH") or os.environ.get("DB_PATH")
    if env_file:
        parent = os.path.dirname(env_file) or "."
        os.makedirs(parent, exist_ok=True)
        return parent, env_file
    data_dir = os.environ.get("DATA_DIR")
    if not data_dir:
        if os.path.isdir("/data"):
            data_dir = "/data"
        else:
            data_dir = os.path.dirname(os.path.abspath(__file__))
    os.makedirs(data_dir, exist_ok=True)
    return data_dir, os.path.join(data_dir, "contratos.db")

_DATA_DIR, DB_PATH = _resolve_data_dir()
UPLOAD_DIR = os.path.join(_DATA_DIR, "uploads")
_STATIC_UPLOAD = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static", "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(_STATIC_UPLOAD, exist_ok=True)
'''

dbp = Path("database.py")
if dbp.exists():
    t = dbp.read_text(encoding="utf-8")
    if "_resolve_data_dir" not in t:
        m = re.search(r"^DB_PATH\s*=.*\n(?:UPLOAD_DIR\s*=.*\n)?", t, re.M)
        if m:
            t = t[: m.start()] + RESOLVE + "\n" + t[m.end() :]
            print("DB_PATH resolve injected")
        else:
            idx = t.find("\n\n")
            if idx > 0:
                t = t[: idx + 2] + RESOLVE + "\n" + t[idx + 2 :]
                print("DB_PATH resolve prepended")
        dbp.write_text(t, encoding="utf-8")
    else:
        print("resolve already present")

def _db_has_data(path):
    try:
        conn = sqlite3.connect(path)
        n = conn.execute("SELECT count(*) FROM sqlite_master WHERE type='table'").fetchone()[0]
        conn.close()
        return n > 0
    except Exception:
        return False

data_dir = os.environ.get("DATA_DIR")
if not data_dir:
    data_dir = "/data" if os.path.isdir("/data") else "."
os.makedirs(data_dir, exist_ok=True)
target = os.environ.get("DATABASE_PATH") or os.environ.get("DB_PATH") or os.path.join(data_dir, "contratos.db")

if not _db_has_data(target):
    for s in (Path("contratos.db"), Path("contratos.db.seed"), Path("seed_contratos.db")):
        if s.exists() and s.stat().st_size > 1000:
            if not Path(target).exists() or Path(target).stat().st_size < 1000:
                shutil.copy2(str(s), target)
                print("seed copied to", target)
            break
    else:
        print("no seed; init_db will create schema at", target)
else:
    print("existing DB kept at", target)

repo_db = Path("contratos.db")
if os.path.isdir("/data") and repo_db.exists() and os.path.abspath(target) != os.path.abspath(str(repo_db)):
    try:
        if not Path("contratos.db.seed").exists():
            repo_db.rename("contratos.db.seed")
            print("renamed repo contratos.db -> contratos.db.seed")
    except Exception as e:
        print("rename skip", e)

print("fix_db_persist done | target=", target)
