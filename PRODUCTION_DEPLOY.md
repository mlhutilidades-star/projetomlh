"""
DEPLOYMENT.md - Guia de Deploy em Produção
Documento consolidado de como deployar HUB Financeiro em produção.
"""

# 🚀 Guia de Deploy em Produção - HUB Financeiro MLH

## 📋 Fase 11: Otimizações Finais e Deploy

Este documento descreve todos os passos necessários para colocar a aplicação HUB Financeiro em produção.

---

## ✅ PRÉ-REQUISITOS

### Hardware Recomendado
- **CPU**: 2+ cores
- **Memória**: 4GB+ RAM
- **Storage**: 50GB+ (SSD recomendado)
- **Rede**: Conexão estável de internet

### Software Recomendado
- **Python**: 3.11+
- **Redis**: 6.0+ (para cache)
- **PostgreSQL**: 12+ (ou SQLite para pequenos deployments)
- **Docker**: 20.10+ (opcional, recomendado)
- **Git**: 2.30+

---

## 🔧 CHECKLIST DE DEPLOY

### 1. Preparação do Ambiente

```bash
# Clonar repositório
git clone https://github.com/mlhutilidades-star/projeto-mlh.git
cd HUB-FINANCEIRO-STREAMLIT

# Criar ambiente virtual
python -m venv venv
source venv/bin/activate  # No Windows: venv\Scripts\activate

# Instalar dependências
pip install -r requirements.txt

# Configurar variáveis de ambiente
cp .env.example .env
# Editar .env com valores de produção
```

### 2. Configuração de Banco de Dados

```bash
# Para SQLite (pequenos deployments)
python -c "from modules.database import init_database; init_database()"

# Para PostgreSQL (production)
export DATABASE_URL="postgresql://user:password@host:5432/mlh_hub"
python -c "from modules.database import init_database; init_database()"
```

### 3. Otimizações de Database

```bash
# Executar otimizações
python scripts/database_optimization.py

# Criar índices necessários
# Criar backups automáticos
# Configurar monitoring
```

### 4. Configuração de Cache (Redis)

```bash
# Instalar Redis (se não estiver)
# Ubuntu: sudo apt-get install redis-server
# MacOS: brew install redis
# Windows: usar WSL ou Docker

# Iniciar Redis
redis-server

# Verificar conexão
redis-cli ping  # Deve retornar PONG
```

### 5. Configuração de Autenticação

```bash
# Editar auth_config.yaml com usuários reais
# Gerar senhas seguras:
python -c "from passlib.context import CryptContext; pwd_cxt = CryptContext(schemes=['bcrypt']); print(pwd_cxt.hash('senha_temporaria'))"

# Configurar OAuth (Shopee, Google, etc.)
# Seguir docs em SHOPEE_OAUTH_SETUP.md
```

### 6. Configuração de Logging

```bash
# Criar diretórios de logs
mkdir -p logs data/metrics

# Configurar rotação de logs
# Editar logging_config.py se necessário

# Centralizar logs (opcional)
# Setup ELK stack ou Splunk
```

### 7. Segurança

```bash
# Gerar chave de encriptação
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key())"

# Armazenar em .env como ENCRYPTION_KEY

# Verificar que secrets não estão versionados
git ls-files | grep -E "(\.env|secrets|keys)" # Não deve retornar nada

# Habilitar HTTPS
# Gerar certificado SSL ou usar Let's Encrypt
# Configurar no Streamlit: config.toml
```

### 8. Rate Limiting (opcional)

```python
# Implementar no app.py antes de main()
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app = limiter.limit("100/minute")(app)
```

### 9. Monitoramento

```bash
# Instalar Prometheus (opcional)
pip install prometheus-client

# Configurar alertas
# Integrar com Grafana para dashboards

# Adicionar health checks
# Configure em /health endpoint
```

### 10. Backup Automático

```bash
# Criar script de backup
#!/bin/bash
BACKUP_DIR="/backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
sqlite3 data/mlh_hub.db ".backup $BACKUP_DIR/backup_$TIMESTAMP.db"
gzip $BACKUP_DIR/backup_$TIMESTAMP.db

# Agendar com cron (Linux/Mac)
crontab -e
0 2 * * * /path/to/backup.sh  # Executar diariamente às 2AM

# ou Windows Task Scheduler
```

---

## 🐳 DEPLOY COM DOCKER

### Dockerfile

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Instalar dependências do sistema
RUN apt-get update && apt-get install -y \
    redis-server \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copiar requirements
COPY requirements.txt .

# Instalar dependências Python
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código
COPY . .

# Expor portas
EXPOSE 8501 6379 5432

# Comando de inicialização
CMD ["streamlit", "run", "app.py", "--server.port=8501"]
```

### Docker Compose

```yaml
version: '3.8'

services:
  app:
    build: .
    ports:
      - "8501:8501"
    environment:
      - DATABASE_URL=postgresql://postgres:password@db:5432/mlh_hub
      - REDIS_URL=redis://redis:6379
    depends_on:
      - db
      - redis
    volumes:
      - ./data:/app/data
      - ./logs:/app/logs

  db:
    image: postgres:13
    environment:
      - POSTGRES_PASSWORD=password
      - POSTGRES_DB=mlh_hub
    volumes:
      - pgdata:/var/lib/postgresql/data

  redis:
    image: redis:6-alpine
    ports:
      - "6379:6379"

volumes:
  pgdata:
```

### Deploy com Docker

```bash
# Build
docker-compose build

# Iniciar
docker-compose up -d

# Verificar logs
docker-compose logs -f app
```

---

## ☁️ DEPLOY EM CLOUD

### Heroku

```bash
# Instalar Heroku CLI
# Login
heroku login

# Criar app
heroku create mlh-financeiro

# Configurar variáveis de ambiente
heroku config:set DATABASE_URL=postgresql://...
heroku config:set REDIS_URL=redis://...

# Deploy
git push heroku main

# Verificar logs
heroku logs --tail
```

### AWS (EC2 + RDS)

```bash
# 1. Provisionar EC2
# 2. Instalar dependências
# 3. Clonar repositório
# 4. Configurar RDS (PostgreSQL)
# 5. Executar migrations
# 6. Iniciar Streamlit com gunicorn

# Usar supervisor para manter processo rodando
```

### Google Cloud (App Engine)

```bash
# Deploy
gcloud app deploy

# Configurar Environment Variables
gcloud app update --set-env-vars DATABASE_URL=...

# Ver logs
gcloud app logs read -f
```

---

## 🔍 VERIFICAÇÃO PÓS-DEPLOY

### Health Checks

```bash
# Verificar conectividade
curl http://localhost:8501/health

# Verificar database
python -c "from modules.database import test_connection; test_connection()"

# Verificar Redis
redis-cli ping

# Verificar APIs
python tests/test_api_connections.py
```

### Testes de Performance

```bash
# Executar stress tests
python tests/test_stress.py

# Validar E2E
python tests/validate_e2e.py

# Coletar métricas
pytest --cov=modules tests/
```

---

## 📊 MONITORAMENTO

### Métricas Importantes

- **Response Time**: Tempo de resposta das requisições
- **Cache Hit Rate**: Porcentagem de acertos de cache
- **Database Queries**: Quantidade e tempo de queries
- **API Errors**: Quantidade de erros de API
- **User Sessions**: Quantidade de usuários ativos

### Alertas Recomendados

- ⚠️ Response time > 5s
- ⚠️ Cache hit rate < 70%
- ⚠️ Database CPU > 80%
- ⚠️ API error rate > 1%
- ⚠️ Disk space < 10%

---

## 🆘 TROUBLESHOOTING

### Problema: App não inicia

```bash
# Verificar logs
streamlit run app.py --logger.level=debug

# Verificar importações
python -c "import streamlit; print(streamlit.__version__)"

# Verificar variáveis de ambiente
env | grep -E "DATABASE|REDIS"
```

### Problema: Database lento

```bash
# Executar ANALYZE
python scripts/database_optimization.py

# Verificar índices
# Verificar query plans
```

### Problema: Cache não funcionando

```bash
# Verificar Redis
redis-cli ping
redis-cli INFO stats

# Limpar cache
redis-cli FLUSHDB

# Reiniciar Redis
redis-cli SHUTDOWN
redis-server
```

---

## 📝 RUNBOOK

### Incident Response

1. **Detectar Problema**: Monitoramento e alertas
2. **Investigar**: Logs, métricas, status dos serviços
3. **Comunicar**: Notificar stakeholders
4. **Resolver**: Aplicar fix ou rollback
5. **Documentar**: Post-mortem e lições aprendidas

### Rollback

```bash
# Em caso de deploy com problema
git revert <commit-hash>
git push origin main

# Ou redeployer versão anterior
docker pull mlh-financeiro:v1.0.0
docker-compose up -d
```

---

## 🎓 Referências

- [Streamlit Deployment Docs](https://docs.streamlit.io/library/deploy)
- [PostgreSQL Best Practices](https://wiki.postgresql.org/wiki/Performance_Optimization)
- [Redis Optimization](https://redis.io/docs/management/optimization/)
- [Docker Best Practices](https://docs.docker.com/develop/dev-best-practices/)

---

## ✅ Checklist Final

- [ ] Todas as variáveis de ambiente configuradas
- [ ] Database migrations executadas
- [ ] Redis iniciado e testado
- [ ] Backups automáticos configurados
- [ ] SSL/TLS habilitado
- [ ] Logging centralizado
- [ ] Monitoramento e alertas ativos
- [ ] Testes de carga executados
- [ ] Runbook de incidentes criado
- [ ] Documentação atualizada
- [ ] Disaster recovery plan testado

---

**Versão**: 1.0.0  
**Data**: 2024  
**Fase**: 11 - Otimizações Finais e Deploy
