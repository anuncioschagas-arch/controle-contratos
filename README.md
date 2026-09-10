# Controle de Contratos

Sistema web de gestão de contratos (CONTRATANTE, CONTRATADO, SETOR, CONTRATO) com:

- Login e perfis (admin / operador / consulta)
- Vínculo de operador a contratante e setor
- Consulta CEP (ViaCEP) e CNPJ (BrasilAPI)
- Geração de PDF de contratos
- Dashboard com totais e vencimentos

## Login padrão

- **Usuário:** `admin`
- **Senha:** `admin123`  
(Altere após o primeiro acesso)

## Executar local

```bash
pip install -r requirements.txt
python app.py
```

Abra http://127.0.0.1:8080

## Publicar online (Render — gratuito)

1. Crie conta em https://render.com e conecte o GitHub
2. **New → Web Service** → selecione este repositório
3. Runtime: **Python**
4. Build: `pip install -r requirements.txt`
5. Start: `python app.py`
6. Deploy

Ou use o arquivo `render.yaml` (Blueprint).

## GitHub

Repositório: https://github.com/anuncioschagas-arch/controle-contratos

## Stack

- Python + Bottle + Jinja2 + SQLite
- ReportLab (PDF)
