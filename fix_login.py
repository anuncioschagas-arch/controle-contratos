#!/usr/bin/env python3
"""Garante login sem marca d'agua cobrindo o formulario."""
from pathlib import Path

LOGIN = '''<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Login — Controle de Contratos</title>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body.login-page {
            display: flex; align-items: center; justify-content: center;
            min-height: 100vh; background: #edf2f7;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Arial, sans-serif;
        }
        .login-box {
            position: relative; z-index: 10; background: #ffffff;
            border-radius: 12px; box-shadow: 0 8px 30px rgba(0,0,0,0.15);
            padding: 2rem 1.75rem; width: 100%; max-width: 400px; margin: 1rem;
            border: 1px solid #e2e8f0;
        }
        .login-box h1 { font-size: 1.35rem; color: #1a365d; margin-bottom: 0.35rem; text-align: center; }
        .login-box .sub { text-align: center; color: #718096; font-size: 0.9rem; margin-bottom: 1.5rem; }
        .alert { padding: 0.7rem 0.9rem; border-radius: 8px; margin-bottom: 1rem; font-size: 0.9rem; }
        .alert-error { background: #fff5f5; color: #c53030; border: 1px solid #feb2b2; }
        .form-group { margin-bottom: 1rem; }
        .form-group label { display: block; font-size: 0.85rem; font-weight: 600; color: #1a365d; margin-bottom: 0.35rem; }
        .form-group input {
            width: 100%; padding: 0.65rem 0.75rem; border: 1px solid #cbd5e0;
            border-radius: 8px; font-size: 1rem; background: #fff; color: #1a202c;
        }
        button[type="submit"] {
            width: 100%; margin-top: 0.5rem; padding: 0.75rem;
            background: #2b6cb0; color: #fff !important; border: none;
            border-radius: 8px; font-size: 1rem; font-weight: 600; cursor: pointer;
        }
        button[type="submit"]:hover { background: #2c5282; }
        .login-hint { margin-top: 1.25rem; font-size: 0.8rem; color: #a0aec0; text-align: center; }
    </style>
</head>
<body class="login-page">
    <div class="login-box">
        <h1>Controle de Contratos</h1>
        <p class="sub">Acesso restrito a usuários autorizados</p>
        {% if message %}
        <div class="alert alert-{{ message_type or 'error' }}">{{ message }}</div>
        {% endif %}
        <form method="post" action="/login">
            <div class="form-group">
                <label for="login">Login</label>
                <input type="text" id="login" name="login" required autofocus autocomplete="username" placeholder="Seu login">
            </div>
            <div class="form-group">
                <label for="senha">Senha</label>
                <input type="password" id="senha" name="senha" required autocomplete="current-password" placeholder="Sua senha">
            </div>
            <button type="submit">Entrar</button>
        </form>
        <p class="login-hint">Política de segurança: sessão autenticada obrigatória</p>
    </div>
</body>
</html>
'''

Path("templates").mkdir(exist_ok=True)
Path("templates/login.html").write_text(LOGIN, encoding="utf-8")
print("login.html rewritten (sem marca d'agua)")
