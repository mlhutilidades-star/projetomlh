# Guia de Implantação - Hub Financeiro

## 🚀 Opções de Deploy

### 1. Streamlit Cloud (Recomendado para início)

**Vantagens:**
- Gratuito
- Deploy automático via GitHub
- SSL automático
- Fácil configuração

**Passos:**

1. **Preparar repositório Git:**
```powershell
cd HUB-FINANCEIRO-STREAMLIT
git init
git add .
git commit -m "Initial commit"
```

2. **Criar repo no GitHub:**
- Acesse github.com
- Crie novo repositório "hub-financeiro"
- Push do código:
```powershell
git remote add origin https://github.com/SEU_USUARIO/hub-financeiro.git
git branch -M main
git push -u origin main
```

3. **Deploy no Streamlit Cloud:**
- Acesse share.streamlit.io
- Login com GitHub
- "New app" → Selecione o repositório
- Main file: `app.py`
- **Secrets:** Adicione variáveis de .env:
  ```toml
  DATABASE_URL = "sqlite:///hub_financeiro.db"
  TINY_API_TOKEN = "seu_token"
  SHOPEE_PARTNER_ID = "seu_id"
  SHOPEE_PARTNER_KEY = "sua_chave"
  SHOPEE_SHOP_ID = "seu_shop_id"
  ```
- Deploy!

**Limitações:**
- Banco SQLite reinicia a cada deploy (considere PostgreSQL)
- Memória limitada (1GB)
- CPU compartilhada

---

### 2. Heroku (Produção escalável)

**Vantagens:**
- PostgreSQL incluído (hobby tier free)
- Escalável
- CLI poderosa

**Requisitos:**
- Conta Heroku (gratuita)
- Heroku CLI instalado

**Passos:**

1. **Instalar Heroku CLI:**
```powershell
winget install Heroku.HerokuCLI
```

2. **Login:**
```powershell
heroku login
```

3. **Criar app:**
```powershell
heroku create hub-financeiro-app
```

4. **Adicionar PostgreSQL:**
```powershell
heroku addons:create heroku-postgresql:mini
```

5. **Criar Procfile:**
```
web: streamlit run app.py --server.port=$PORT --server.address=0.0.0.0
```

6. **Criar runtime.txt:**
```
python-3.13.0
```

7. **Configurar variáveis:**
```powershell
heroku config:set TINY_API_TOKEN=seu_token
heroku config:set SHOPEE_PARTNER_ID=seu_id
# ... outras variáveis
```

8. **Ajustar database.py para PostgreSQL:**
```python
# Trocar de sqlite para postgres
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///hub_financeiro.db")
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)
```

9. **Deploy:**
```powershell
git add .
git commit -m "Heroku config"
git push heroku main
```

10. **Inicializar banco:**
```powershell
heroku run python -c "from modules.database import init_database; init_database()"
```

**Acesso:**
```
https://hub-financeiro-app.herokuapp.com
```

---

### 3. AWS EC2 (Controle total)

**Vantagens:**
- Controle completo do servidor
- Escalável
- VPC, security groups

**Passos resumidos:**

1. **Criar instância EC2:**
- Ubuntu 22.04 LTS
- t2.micro (free tier)
- Security Group: Portar 8501 (ou 80/443)

2. **Conectar via SSH:**
```powershell
ssh -i sua-chave.pem ubuntu@seu-ip-publico
```

3. **Instalar dependências:**
```bash
sudo apt update
sudo apt install python3.11 python3-pip nginx -y
```

4. **Clonar projeto:**
```bash
cd /var/www
git clone https://github.com/SEU_USUARIO/hub-financeiro.git
cd hub-financeiro
```

5. **Setup ambiente:**
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

6. **Configurar .env:**
```bash
nano .env
# Adicionar credenciais
```

7. **Criar serviço systemd:**
```bash
sudo nano /etc/systemd/system/hubfinanceiro.service
```
```ini
[Unit]
Description=Hub Financeiro Streamlit
After=network.target

[Service]
User=ubuntu
WorkingDirectory=/var/www/hub-financeiro
Environment="PATH=/var/www/hub-financeiro/venv/bin"
ExecStart=/var/www/hub-financeiro/venv/bin/streamlit run app.py --server.port=8501

[Install]
WantedBy=multi-user.target
```

8. **Iniciar serviço:**
```bash
sudo systemctl enable hubfinanceiro
sudo systemctl start hubfinanceiro
```

9. **Configurar Nginx (reverse proxy):**
```bash
sudo nano /etc/nginx/sites-available/hubfinanceiro
```
```nginx
server {
    listen 80;
    server_name seu-dominio.com;
    
    location / {
        proxy_pass http://localhost:8501;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
    }
}
```

```bash
sudo ln -s /etc/nginx/sites-available/hubfinanceiro /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

10. **(Opcional) SSL com Let's Encrypt:**
```bash
sudo apt install certbot python3-certbot-nginx -y
sudo certbot --nginx -d seu-dominio.com
```

**Acesso:**
```
http://seu-dominio.com
```

---

### 4. Docker (Portabilidade)

**Criar Dockerfile:**
```dockerfile
FROM python:3.13-slim

WORKDIR /app

# Dependências do sistema (OCR opcional)
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    poppler-utils \
    && rm -rf /var/lib/apt/lists/*

# Dependências Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Código da aplicação
COPY . .

# Criar diretório de logs
RUN mkdir -p logs

# Expor porta
EXPOSE 8501

# Comando de inicialização
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

**Criar .dockerignore:**
```
venv/
__pycache__/
*.pyc
.env
hub_financeiro.db
logs/
.git/
```

**Criar docker-compose.yml:**
```yaml
version: '3.8'

services:
  web:
    build: .
    ports:
      - "8501:8501"
    environment:
      - DATABASE_URL=postgresql://user:pass@db:5432/hubfinanceiro
      - TINY_API_TOKEN=${TINY_API_TOKEN}
      - SHOPEE_PARTNER_ID=${SHOPEE_PARTNER_ID}
      - SHOPEE_PARTNER_KEY=${SHOPEE_PARTNER_KEY}
      - SHOPEE_SHOP_ID=${SHOPEE_SHOP_ID}
    volumes:
      - ./logs:/app/logs
    depends_on:
      - db
  
  db:
    image: postgres:15
    environment:
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=pass
      - POSTGRES_DB=hubfinanceiro
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  postgres_data:
```

**Build e run:**
```powershell
docker-compose up --build
```

**Acesso:**
```
http://localhost:8501
```

---

## 🔐 Configuração de Segurança

### 1. Variáveis de Ambiente

**Nunca commitar .env!**

Sempre use:
- Streamlit Cloud: Secrets
- Heroku: Config Vars
- AWS: Parameter Store ou Secrets Manager
- Docker: env_file ou docker-compose environment

### 2. Autenticação (Opcional)

**Adicionar ao requirements.txt:**
```
streamlit-authenticator==0.2.3
```

**Criar users.yaml:**
```yaml
credentials:
  usernames:
    admin:
      name: Administrador
      password: $2b$12$hashed_password_aqui  # Use bcrypt
```

**Modificar app.py:**
```python
import streamlit_authenticator as stauth

# Carregar configuração
with open('users.yaml') as file:
    config = yaml.safe_load(file)

authenticator = stauth.Authenticate(
    config['credentials'],
    'hub_financeiro_cookie',
    'secret_key_aleatorio',
    cookie_expiry_days=30
)

name, authentication_status, username = authenticator.login('Login', 'main')

if authentication_status:
    st.write(f'Bem-vindo *{name}*')
    # ... resto do app
elif authentication_status == False:
    st.error('Usuário/senha incorretos')
elif authentication_status == None:
    st.warning('Por favor, faça login')
    st.stop()
```

### 3. HTTPS

**Streamlit Cloud:** Automático  
**Heroku:** Automático  
**AWS:** Usar Nginx + Let's Encrypt (ver passo 10 acima)  
**Docker:** Usar reverse proxy (Nginx/Traefik)

---

## 📊 Backup e Recuperação

### 1. Banco de Dados

**SQLite (local):**
```powershell
# Backup manual
copy hub_financeiro.db backups\hub_financeiro_$(Get-Date -Format 'yyyyMMdd').db

# Backup automático (Task Scheduler)
# Criar script backup.ps1:
$date = Get-Date -Format "yyyyMMdd_HHmmss"
copy hub_financeiro.db "backups\hub_financeiro_$date.db"
```

**PostgreSQL (Heroku):**
```powershell
# Backup
heroku pg:backups:capture
heroku pg:backups:download

# Restaurar
heroku pg:backups:restore backup-url DATABASE_URL
```

### 2. Arquivos de Log

**Rotação automática:**
- Os logs já usam nome diário (`app_YYYYMMDD.log`)
- Criar script de limpeza:

```powershell
# limpar_logs_antigos.ps1
$dias = 30
Get-ChildItem logs\app_*.log | Where-Object { 
    $_.LastWriteTime -lt (Get-Date).AddDays(-$dias) 
} | Remove-Item
```

---

## 📈 Monitoramento

### 1. Logs Centralizados

**Opções:**
- **Papertrail** (free tier)
- **Loggly**
- **CloudWatch** (AWS)

**Configuração (Papertrail exemplo):**
```python
# modules/logging_config.py
from logging.handlers import SysLogHandler

# Adicionar handler remoto
papertrail_handler = SysLogHandler(address=('logs.papertrailapp.com', 12345))
logger.addHandler(papertrail_handler)
```

### 2. Uptime Monitoring

**Opções:**
- **UptimeRobot** (free)
- **Pingdom**
- **StatusCake**

Configurar ping HTTP a cada 5 minutos em:
```
https://seu-app.herokuapp.com
```

### 3. Performance Monitoring

**Streamlit tem métricas built-in:**
- Adicionar ao sidebar:
```python
if st.checkbox("📊 Mostrar Métricas"):
    st.metric("Tempo de carregamento", f"{st.runtime.stats.get('query_time', 0):.2f}s")
```

---

## 🔄 CI/CD (Continuous Deployment)

### GitHub Actions

**Criar .github/workflows/deploy.yml:**
```yaml
name: Deploy to Streamlit Cloud

on:
  push:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.13'
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
    - name: Run tests
      run: |
        python tests/test_runner.py
        python tests/validate_e2e.py
```

---

## 📞 Troubleshooting de Deploy

### Problema: Streamlit Cloud não inicia
**Solução:**
- Verificar logs em "Manage app" → "Logs"
- Confirmar requirements.txt correto
- Verificar secrets configurados

### Problema: Heroku Database error
**Solução:**
```powershell
heroku logs --tail
heroku pg:info
heroku run python -c "from modules.database import init_database; init_database()"
```

### Problema: AWS EC2 não acessível
**Solução:**
- Verificar Security Group (porta 80/8501 aberta)
- Verificar serviço: `sudo systemctl status hubfinanceiro`
- Verificar nginx: `sudo nginx -t`

---

## ✅ Checklist de Deploy

- [ ] Código no Git (sem .env commitado)
- [ ] Testes passando (test_runner, validate_e2e)
- [ ] Variáveis de ambiente configuradas
- [ ] Banco de dados criado (se externo)
- [ ] Dependências instaladas (requirements.txt)
- [ ] Logs configurados
- [ ] HTTPS habilitado (produção)
- [ ] Backup configurado
- [ ] Monitoramento configurado
- [ ] Autenticação configurada (se multi-usuário)
- [ ] README.md atualizado com URL de produção

---

**Pronto! Seu Hub Financeiro está no ar! 🚀**

---

## 🔧 Apêndice — Segurança, Observabilidade e Arquitetura

### Checklist de Segredos (.env)

No arquivo `.env` mantenha apenas o necessário e NUNCA publique:

```
# Shopee OAuth
SHOPEE_PARTNER_ID=
SHOPEE_PARTNER_KEY=
SHOPEE_SHOP_ID=
SHOPEE_REDIRECT_URL=
SHOPEE_ACCESS_TOKEN=
SHOPEE_REFRESH_TOKEN=

# Tiny ERP
TINY_API_TOKEN=

# Banco de dados
DATABASE_URL=sqlite:///hub_financeiro.db

# Logging e cache
LOG_LEVEL=INFO
CACHE_TTL=300
```

Rotacione tokens periodicamente e restrinja logs para não expor credenciais.

### Observabilidade e Métricas

- Logging em JSON com níveis configuráveis (`LOG_LEVEL`).
- Métricas estilo Prometheus (contadores/gauges) e medição de duração de funções.
- Health checks disponíveis na página `📊 Metricas` dentro do app.

### Arquitetura (Resumo)

- Domain / Infrastructure / Services: entidades de negócio separadas dos repositórios SQLAlchemy e dos serviços que orquestram regras.
- Deduplicação determinística via hash SHA256 truncado (16 chars), armazenado como `HASH:{hash}`.
- Analytics com filtros por período, categoria e status e cache TTL configurável.
- Sincronizações Tiny ERP e Shopee com paginação por cursor e janelas de tempo para limites de API.

### Verificação rápida

```powershell
# Subir app em modo headless
streamlit run app.py --server.headless true --server.port 8501

# Rodar suíte completa de testes
pytest -q
```

