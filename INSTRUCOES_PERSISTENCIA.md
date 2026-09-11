# Persistência de dados no Render (plano gratuito)

O plano **free** do Render **não permite** Persistent Disk.
Por isso o SQLite local some a cada deploy/reinício.

## Solução: PostgreSQL gratuito (Neon)

### 1. Criar banco no Neon (grátis)
1. Acesse https://neon.tech e crie uma conta
2. Create project → copie a **connection string**
   (ex.: `postgresql://user:senha@ep-xxx.region.aws.neon.tech/neondb?sslmode=require`)

### 2. Configurar no Render
1. Render → serviço **controle-contratos** → **Environment**
2. Add Environment Variable:
   - **Key:** `DATABASE_URL`
   - **Value:** (cole a connection string do Neon)
3. **Manual Deploy** → Deploy latest commit

### 3. Conferir
Nos logs deve aparecer: `DATABASE_URL detectado — usando PostgreSQL`.
Cadastros e edições passam a **permanecer** após deploy/reinício.

## Alternativa paga
Plano do Render com Disk em `/data` e variável `DATA_DIR=/data`.
