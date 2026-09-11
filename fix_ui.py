#!/usr/bin/env python3
"""Garante static/style.css com marca d'agua discreta no canto."""
from pathlib import Path

static = Path("static")
static.mkdir(exist_ok=True)
(static / "uploads").mkdir(exist_ok=True)

CSS = r'''/* Controle de Contratos */
:root { --primary:#1a365d; --primary-light:#2b6cb0; --bg:#f7fafc; --card:#fff; --border:#e2e8f0; --text:#1a202c; --muted:#718096; }
* { box-sizing:border-box; margin:0; padding:0; }
body { font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Arial,sans-serif; background:var(--bg); color:var(--text); line-height:1.5; min-height:100vh; }
.marca-dagua { position:fixed; right:1rem; bottom:1rem; width:min(220px,28vw); opacity:0.12; z-index:0; pointer-events:none; object-fit:contain; }
.navbar { background:#1a365d; color:#fff; padding:0.85rem 1.25rem; display:flex; flex-wrap:wrap; align-items:center; gap:0.5rem 1rem; position:sticky; top:0; z-index:100; }
.navbar .brand { color:#fff; font-weight:700; text-decoration:none; }
.navbar nav a { color:rgba(255,255,255,0.92); text-decoration:none; padding:0.3rem 0.55rem; border-radius:4px; font-size:0.9rem; }
.navbar nav a:hover { background:rgba(255,255,255,0.15); }
.container { max-width:1100px; margin:0 auto; padding:1.25rem 1rem; position:relative; z-index:1; }
.card, .stat-card { background:#fff; border:1px solid var(--border); border-radius:10px; padding:1.1rem; margin-bottom:1rem; position:relative; z-index:1; }
.stats { display:grid; grid-template-columns:repeat(auto-fill,minmax(160px,1fr)); gap:0.85rem; margin-bottom:1.25rem; }
.stat-card .number { font-size:1.6rem; font-weight:700; color:#2b6cb0; }
.stat-card .label { font-size:0.85rem; color:#718096; }
.btn { display:inline-block; padding:0.45rem 0.9rem; border-radius:6px; border:1px solid transparent; cursor:pointer; font-size:0.9rem; text-decoration:none; }
.btn-primary { background:#2b6cb0; color:#fff; }
.btn-outline { background:#fff; border-color:#cbd5e0; color:#2d3748; }
.btn-danger { background:#e53e3e; color:#fff; }
.btn-sm { padding:0.25rem 0.55rem; font-size:0.8rem; }
.form-grid { display:grid; grid-template-columns:1fr 1fr; gap:0.85rem; }
.form-group.full { grid-column:1/-1; }
.form-group label { display:block; font-size:0.85rem; font-weight:600; color:#1a365d; margin-bottom:0.3rem; }
.form-group input, .form-group select, .form-group textarea { width:100%; padding:0.5rem 0.65rem; border:1px solid #e2e8f0; border-radius:6px; }
.form-actions { margin-top:1rem; display:flex; gap:0.5rem; }
table { width:100%; border-collapse:collapse; background:#fff; }
th, td { padding:0.55rem 0.65rem; border-bottom:1px solid #e2e8f0; text-align:left; font-size:0.9rem; }
th { background:#f7fafc; color:#1a365d; }
.alert { padding:0.75rem 1rem; border-radius:8px; margin-bottom:1rem; }
.alert-error { background:#fff5f5; color:#c53030; border:1px solid #feb2b2; }
.alert-info { background:#ebf8ff; color:#2b6cb0; border:1px solid #90cdf4; }
.badge { display:inline-block; padding:0.15rem 0.45rem; border-radius:999px; font-size:0.75rem; }
.badge-vencido { background:#c6f6d5; color:#276749; }
.badge-encerrado { background:#fefcbf; color:#975a16; }
.badge-cancelado { background:#fed7d7; color:#c53030; }
.footer { text-align:center; color:#a0aec0; font-size:0.8rem; padding:1.5rem; }
.page-header { display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:0.75rem; margin-bottom:1.25rem; }
.page-header h1 { font-size:1.4rem; color:#1a365d; }
@media (max-width:700px){ .form-grid { grid-template-columns:1fr; } }
'''
Path("static/style.css").write_text(CSS, encoding="utf-8")
print("style.css written", Path("static/style.css").stat().st_size)
print("fix_ui done")
