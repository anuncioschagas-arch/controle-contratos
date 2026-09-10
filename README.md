# Controle de Contratos

Sistema web de gestão de contratos com login, perfis, CEP/CNPJ e PDF.

**Repositório:** https://github.com/anuncioschagas-arch/controle-contratos

## Base de dados

Os dados do arquivo `contratos.db` fornecido foram exportados para o pacote do app (seed).

## Login padrão

- Usuário: `admin`
- Senha: `admin123`

## Colocar online (Render.com) — recomendado

O Global Market Radar era site **estático** (HTML no GitHub Pages).
Este app é **Python (Bottle + SQLite)** e precisa de um servidor. Use o **Render** (gratuito):

1. Acesse https://render.com e entre com a conta **GitHub** (`anuncioschagas-arch`)
2. **New +** → **Web Service**
3. Conecte o repositório `controle-contratos`
4. Configure:
   - **Runtime:** Python 3
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `bash start.sh`
5. Em Environment (opcional):
   - `HOST` = `0.0.0.0`
   - `CONTRATOS_SECRET` = (texto secreto longo)
6. **Create Web Service** e aguarde o deploy

A URL pública será algo como:
`https://controle-contratos.onrender.com`

## Código-fonte completo

Use o arquivo `controle_contratos_src.zip` do projeto e envie para o GitHub:

```bash
git clone https://github.com/anuncioschagas-arch/controle-contratos.git
cd controle-contratos
unzip controle_contratos_src.zip
git add .
git commit -m "App completo + base de dados"
git push
```

Depois faça **Manual Deploy** no Render.

## Executar local

```bash
pip install -r requirements.txt
python app.py
```
