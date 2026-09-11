#!/usr/bin/env python3
"""Corrige 500 em /contratos/<id>: template usa item, rota passava so c."""
from pathlib import Path

app = Path("app.py")
if app.exists():
    t = app.read_text(encoding="utf-8")
    changed = False
    for old, new in [
        ('return render("ver_contrato.html", c=c)', 'return render("ver_contrato.html", c=c, item=c)'),
        ("return render('ver_contrato.html', c=c)", "return render('ver_contrato.html', c=c, item=c)"),
    ]:
        if old in t and "item=c" not in t[t.find("def ver_contrato"): t.find("def ver_contrato") + 350]:
            t = t.replace(old, new)
            changed = True
            print("replaced render")
    if changed:
        app.write_text(t, encoding="utf-8")
        print("app.py updated")
    else:
        if "item=c" in t:
            print("ver_contrato already ok")
        else:
            import re
            t2, n = re.subn(
                r'return render\(["\']ver_contrato\.html["\']\s*,\s*c=c\s*\)',
                'return render("ver_contrato.html", c=c, item=c)',
                t,
                count=1,
            )
            if n:
                app.write_text(t2, encoding="utf-8")
                print("regex fixed")
            else:
                print("pattern miss")

Path("templates").mkdir(exist_ok=True)
Path("templates/ver_contrato.html").write_text("""{% extends "base.html" %}
{% block title %}Contrato {{ item.numero }} — Controle de Contratos{% endblock %}
{% block content %}
<div class="page-header">
    <h1>Contrato {{ item.numero }}</h1>
    <div class="btn-group">
        <a href="/contratos/{{ item.id }}/pdf" class="btn btn-success" target="_blank">Gerar PDF</a>
        <a href="/contratos/{{ item.id }}/editar" class="btn btn-outline">Editar</a>
        <a href="/contratos" class="btn btn-outline">← Voltar</a>
    </div>
</div>
<div class="card">
    <p style="margin-bottom:1rem;">
        Status: <span class="badge badge-{{ (item.status or '')|lower }}">{{ item.status }}</span>
        {% if item.operador_nome %} | Operador: <strong>{{ item.operador_nome }}</strong>{% endif %}
    </p>
    <div style="display:grid;grid-template-columns:1fr 1fr;gap:1rem;">
        <div>
            <h3 style="color:#1a365d;">Contratante</h3>
            <p><strong>{{ item.contratante_nome or '—' }}</strong></p>
            <p>Doc: {{ item.contratante_doc or '—' }}</p>
        </div>
        <div>
            <h3 style="color:#1a365d;">Contratado</h3>
            <p><strong>{{ item.contratado_nome or '—' }}</strong></p>
            <p>Doc: {{ item.contratado_doc or '—' }}</p>
        </div>
    </div>
    <hr style="margin:1.25rem 0;border:none;border-top:1px solid #e2e8f0;">
    <p><strong>Setor:</strong> {{ item.setor_nome or '—' }}</p>
    <p><strong>Objeto:</strong> {{ item.objeto or '—' }}</p>
    <p><strong>Vigência:</strong> {{ item.data_inicio or '—' }} até {{ item.data_fim or '—' }}</p>
    <p><strong>Meses:</strong> {{ item.quantidade_meses or '—' }}</p>
    <p><strong>Valor mensal:</strong> {% if item.valor_mensal %}R$ {{ '%.2f'|format(item.valor_mensal)|replace('.', ',') }}{% else %}—{% endif %}</p>
    <p><strong>Valor total:</strong> {% if item.valor %}R$ {{ '%.2f'|format(item.valor)|replace('.', ',') }}{% else %}—{% endif %}</p>
    {% if item.observacoes %}<p><strong>Observações:</strong> {{ item.observacoes }}</p>{% endif %}
</div>
{% endblock %}
""", encoding="utf-8")
print("ver_contrato.html written")
print("fix_ver_contrato done")
