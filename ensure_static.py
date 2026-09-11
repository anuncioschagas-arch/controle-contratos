#!/usr/bin/env python3
"""Garante static/style.css no boot."""
from pathlib import Path

static = Path("static")
static.mkdir(exist_ok=True)
(static / "uploads").mkdir(exist_ok=True)

css = static / "style.css"
if not css.exists() or css.stat().st_size < 500:
    css.write_text(""":root { --primary:#2b6cb0; --dark:#1a365d; --bg:#edf2f7; --card:#fff; --border:#e2e8f0; }
* { box-sizing: border-box; }
body { margin:0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background: var(--bg); color:#1a202c; }
.navbar { background:#1a365d; color:#fff; padding:0.75rem 1.25rem; display:flex; flex-wrap:wrap; align-items:center; gap:0.75rem; position:relative; z-index:10; }
.navbar a { color:#e2e8f0; text-decoration:none; margin-right:0.75rem; font-size:0.9rem; }
.navbar a:hover { color:#fff; }
.navbar .brand { color:#fff; font-weight:700; margin-right:1rem; text-decoration:none; }
.container { max-width:1100px; margin:1.25rem auto; padding:0 1rem; position:relative; z-index:1; }
.card { background:var(--card); border:1px solid var(--border); border-radius:10px; padding:1.25rem; margin-bottom:1rem; box-shadow:0 1px 3px rgba(0,0,0,.06); }
.btn { display:inline-block; padding:0.45rem 0.9rem; border-radius:6px; border:1px solid transparent; cursor:pointer; font-size:0.9rem; text-decoration:none; }
.btn-primary { background:#2b6cb0; color:#fff; }
.btn-outline { background:#fff; border-color:#cbd5e0; color:#2d3748; }
.btn-danger { background:#e53e3e; color:#fff; }
.btn-sm { padding:0.25rem 0.55rem; font-size:0.8rem; }
.form-grid { display:grid; grid-template-columns:1fr 1fr; gap:0.85rem; }
.form-group.full { grid-column:1 / -1; }
.form-group label { display:block; font-size:0.85rem; font-weight:600; color:#1a365d; margin-bottom:0.3rem; }
.form-group input, .form-group select, .form-group textarea { width:100%; padding:0.5rem 0.65rem; border:1px solid #e2e8f0; border-radius:6px; }
.form-actions { margin-top:1rem; display:flex; gap:0.5rem; }
.alert { padding:0.75rem 1rem; border-radius:8px; margin-bottom:1rem; }
.alert-error { background:#fff5f5; color:#c53030; border:1px solid #feb2b2; }
.alert-info { background:#ebf8ff; color:#2b6cb0; border:1px solid #90cdf4; }
.page-header { display:flex; justify-content:space-between; align-items:center; margin-bottom:1rem; gap:1rem; flex-wrap:wrap; }
.page-header h1 { font-size:1.35rem; color:#1a365d; margin:0; }
table { width:100%; border-collapse:collapse; }
th, td { padding:0.55rem 0.65rem; border-bottom:1px solid #e2e8f0; text-align:left; font-size:0.9rem; }
th { background:#f7fafc; color:#1a365d; }
.badge { display:inline-block; padding:0.15rem 0.45rem; border-radius:999px; font-size:0.75rem; }
.footer { text-align:center; color:#a0aec0; font-size:0.8rem; padding:1.5rem; }
.marca-dagua { position:fixed; top:50%; left:50%; transform:translate(-50%,-50%); width:min(900px,90vw); opacity:0.22; z-index:0; pointer-events:none; }
@media (max-width:700px){ .form-grid { grid-template-columns:1fr; } }
""", encoding="utf-8")
    print("style.css created")
else:
    print("style.css ok", css.stat().st_size)
print("ensure_static done")
