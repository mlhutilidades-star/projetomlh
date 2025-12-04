# CLOUD DEPLOYMENT GUIDE - HUB-FINANCEIRO-STREAMLIT

## Visão Geral

Este documento fornece estratégias de deployment para as plataformas de cloud mais populares (AWS, Azure, GCP). O HUB-FINANCEIRO-STREAMLIT é uma aplicação Streamlit que integra APIs (Shopee, Tiny ERP) com processamento de PDFs e análise financeira em tempo real.

---

## PRÉ-REQUISITOS GLOBAIS

### Dependências
- Python 3.10+ (recomendado 3.13)
- pip >= 23.0
- Git
- Docker (opcional, mas recomendado)

### Variáveis de Ambiente Necessárias
```bash
# API Keys
SHOPEE_API_KEY=your_shopee_api_key
SHOPEE_API_SECRET=your_shopee_api_secret
TINY_API_TOKEN=your_tiny_erp_token

# Autenticação OAuth (Shopee)
SHOPEE_SHOP_ID=your_shop_id
SHOPEE_REFRESH_TOKEN=your_refresh_token

# Configuração de Ambiente
ENVIRONMENT=production
LOG_LEVEL=INFO
DATABASE_URL=your_database_url (opcional)

# Streamlit
STREAMLIT_SERVER_PORT=8501
STREAMLIT_SERVER_HEADLESS=true
STREAMLIT_CLIENT_TOOLBARPOSITION=minimal
```

### Secrets Management
Use **AWS Secrets Manager**, **Azure Key Vault**, ou **Google Secret Manager** para armazenar senhas e tokens.

---

## OPÇÃO 1: AWS - ELASTIC BEANSTALK

### Descrição
AWS Elastic Beanstalk é PaaS (Platform as a Service) que gerencia automáticamente instâncias EC2, load balancing e auto-scaling.

### Arquitetura
```
Route 53 (DNS)
    ↓
CloudFront (CDN)
    ↓
Elastic Load Balancer (ALB)
    ↓
Elastic Beanstalk Environment
    ├─ EC2 Instances (Auto-scaling)
    ├─ Secrets Manager (API Keys)
    └─ CloudWatch (Logs & Metrics)
```

### Setup & Deployment

#### 1. Preparar Aplicação
```bash
# Criar .ebextensions/python.config
mkdir -p .ebextensions

cat > .ebextensions/python.config << 'EOF'
option_settings:
  aws:elasticbeanstalk:container:python:
    WSGIPath: "app:app"
  aws:elasticbeanstalk:application:environment:
    PYTHONPATH: "/var/app/current:$PYTHONPATH"
  aws:elasticbeanstalk:cloudwatch:logs:
    StreamLogs: true
    DeleteOnTerminate: false
    RetentionInDays: 30

commands:
  01_install_requirements:
    command: "pip install -r requirements.txt --no-cache-dir"

container_commands:
  01_migrate:
    command: "python -m pytest tests/ -q --tb=no"
    leader_only: true
EOF
```

#### 2. Criar Dockerfile Alternativo
```dockerfile
FROM python:3.13-slim

WORKDIR /app

# Copiar requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código
COPY . .

# Expor porta Streamlit
EXPOSE 8501

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
  CMD python -c "import requests; requests.get('http://localhost:8501')"

# Rodar Streamlit
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.headless=true"]
```

#### 3. Arquivo de Configuração AWS
```bash
# .ebextensions/aws.config
option_settings:
  aws:autoscaling:launchconfiguration:
    InstanceType: t3.medium
    RootVolumeSize: 32
  aws:elasticbeanstalk:environment:
    EnvironmentType: LoadBalanced
    LoadBalancerType: application
    MaxInstanceCount: 4
    MinInstanceCount: 2
  aws:elasticbeanstalk:cloudwatch:logs:
    StreamLogs: true

Resources:
  SecurityGroup:
    Type: "AWS::EC2::SecurityGroup"
    Properties:
      GroupDescription: "Security group for Streamlit"
      SecurityGroupIngress:
        - IpProtocol: tcp
          FromPort: 8501
          ToPort: 8501
          CidrIp: "0.0.0.0/0"
```

#### 4. Deployment
```bash
# Instalar CLI
pip install awsebcli

# Inicializar ambiente
eb init -p python-3.13 hub-financeiro --region us-east-1

# Criar ambiente
eb create production-env --instance-type t3.medium --envvars \
  SHOPEE_API_KEY=xxx,TINY_API_TOKEN=yyy

# Deploy
eb deploy

# Ver logs
eb logs --stream

# Scale up
eb scale 3
```

#### 5. Configurar Secrets Manager
```bash
# Armazenar chaves
aws secretsmanager create-secret \
  --name hub-financeiro/shopee-api \
  --secret-string '{"api_key":"xxx","api_secret":"yyy"}'

# Recuperar em código
import boto3
client = boto3.client('secretsmanager')
secret = client.get_secret_value(SecretId='hub-financeiro/shopee-api')
```

#### 6. Monitorar
```bash
# CloudWatch Metrics
- CPU Utilization
- Memory Utilization
- HTTP Request Count
- Error Rate

# Alarms
- CPU > 75% → Scale up
- Error Rate > 5% → Alert
- Response Time > 5s → Alert
```

### Estimativa de Custos AWS
- **t3.medium**: $0.0416/hora (~$30/mês)
- **Data Transfer**: ~$0.09/GB
- **Secrets Manager**: $0.40/secret/mês
- **CloudWatch**: ~$5/mês
- **Total**: ~$45-60/mês

---

## OPÇÃO 2: AZURE - APP SERVICE

### Descrição
Azure App Service oferece hosting gerenciado com suporte nativo para Python com Streamlit.

### Arquitetura
```
Azure Front Door (CDN)
    ↓
Application Gateway (Load Balancer)
    ↓
App Service Plan
    ├─ Web App (Streamlit)
    ├─ Key Vault (Secrets)
    └─ Application Insights (Monitoring)
```

### Setup & Deployment

#### 1. Preparar Azure CLI
```bash
# Instalar CLI
pip install azure-cli

# Login
az login

# Criar resource group
az group create \
  --name hub-financeiro-rg \
  --location eastus
```

#### 2. Criar App Service Plan
```bash
# App Service Plan
az appservice plan create \
  --name hub-financeiro-plan \
  --resource-group hub-financeiro-rg \
  --sku B2 \
  --is-linux

# Web App
az webapp create \
  --resource-group hub-financeiro-rg \
  --plan hub-financeiro-plan \
  --name hub-financeiro-app \
  --runtime "PYTHON:3.13"
```

#### 3. Arquivo de Configuração
```bash
# .azure/config.json
{
  "appName": "hub-financeiro-app",
  "resourceGroup": "hub-financeiro-rg",
  "plan": "hub-financeiro-plan",
  "pythonVersion": "3.13",
  "startupCommand": "python -m streamlit run app.py --server.port 8000"
}
```

#### 4. Startup Script
```bash
# startup.sh
#!/bin/bash
set -e

# Install dependencies
python -m pip install --upgrade pip
pip install -r requirements.txt

# Run tests
python -m pytest tests/ -q --tb=no

# Start application
python -m streamlit run app.py \
  --server.port 8000 \
  --server.address 0.0.0.0 \
  --server.headless true
```

#### 5. Deployment via GitHub Actions
```bash
# .github/workflows/azure-deploy.yml
name: Deploy to Azure App Service

on:
  push:
    branches: [master]

jobs:
  deploy:
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
          pip install azure-cli
      
      - name: Run tests
        run: |
          python -m pytest tests/ -q
      
      - name: Deploy to Azure
        env:
          AZURE_CREDENTIALS: ${{ secrets.AZURE_CREDENTIALS }}
        run: |
          az login --service-principal -u ${{ secrets.AZURE_CLIENT_ID }} \
            -p ${{ secrets.AZURE_CLIENT_SECRET }} \
            --tenant ${{ secrets.AZURE_TENANT_ID }}
          az webapp up \
            --resource-group hub-financeiro-rg \
            --name hub-financeiro-app
```

#### 6. Configurar Key Vault
```bash
# Criar Key Vault
az keyvault create \
  --name hub-financeiro-kv \
  --resource-group hub-financeiro-rg

# Adicionar secrets
az keyvault secret set \
  --vault-name hub-financeiro-kv \
  --name shopee-api-key \
  --value "xxx"

# Dar acesso à App Service
az webapp identity assign \
  --resource-group hub-financeiro-rg \
  --name hub-financeiro-app

az keyvault set-policy \
  --name hub-financeiro-kv \
  --object-id <SERVICE_PRINCIPAL_ID> \
  --secret-permissions get list
```

#### 7. Monitorar
```bash
# Application Insights
az monitor app-insights component create \
  --app hub-financeiro-insights \
  --location eastus \
  --resource-group hub-financeiro-rg

# Ver logs
az webapp log tail \
  --resource-group hub-financeiro-rg \
  --name hub-financeiro-app
```

### Estimativa de Custos Azure
- **App Service (B2)**: $0.141/hora (~$100/mês)
- **Key Vault**: $0.60/mês (até 2400 ops/mês)
- **Application Insights**: Até $5/mês
- **Data Transfer**: Gratuito (ingress), ~$0.12/GB (egress)
- **Total**: ~$110-130/mês

---

## OPÇÃO 3: GOOGLE CLOUD - CLOUD RUN

### Descrição
Google Cloud Run é serverless e executa containers Docker com auto-scaling automático e pricing por uso.

### Arquitetura
```
Cloud CDN
    ↓
Cloud Load Balancing
    ↓
Cloud Run Service
    ├─ Container (Streamlit)
    ├─ Secret Manager (Credentials)
    └─ Cloud Logging (Logs)
```

### Setup & Deployment

#### 1. Preparar Google Cloud
```bash
# Instalar SDK
curl https://sdk.cloud.google.com | bash

# Login
gcloud auth login

# Criar projeto
gcloud projects create hub-financeiro --name="Hub Financeiro"

# Ativar APIs
gcloud services enable run.googleapis.com
gcloud services enable container.googleapis.com
gcloud services enable secretmanager.googleapis.com
```

#### 2. Criar Dockerfile Otimizado
```dockerfile
FROM python:3.13-slim

# Variáveis de build
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# Copiar requirements
COPY requirements.txt .

# Instalar dependências
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# Copiar código
COPY . .

# Health check
HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
  CMD python -c "import requests; requests.get('http://localhost:8080')" || exit 1

# Expor porta
EXPOSE 8080

# Streamlit config
ENV STREAMLIT_SERVER_PORT=8080 \
    STREAMLIT_SERVER_ADDRESS=0.0.0.0 \
    STREAMLIT_SERVER_HEADLESS=true \
    STREAMLIT_CLIENT_TOOLBARPOSITION=minimal

# Rodar app
CMD exec streamlit run app.py
```

#### 3. Build e Push para Container Registry
```bash
# Configurar projeto
gcloud config set project hub-financeiro

# Build image
docker build -t gcr.io/hub-financeiro/app:latest .

# Autenticar Docker
gcloud auth configure-docker

# Push para GCR
docker push gcr.io/hub-financeiro/app:latest
```

#### 4. Deploy para Cloud Run
```bash
# Deploy via gcloud
gcloud run deploy hub-financeiro \
  --image gcr.io/hub-financeiro/app:latest \
  --platform managed \
  --region us-central1 \
  --memory 512Mi \
  --cpu 1 \
  --allow-unauthenticated \
  --set-env-vars "LOG_LEVEL=INFO" \
  --timeout 3600 \
  --concurrency 50 \
  --max-instances 10 \
  --min-instances 1

# Resultado
# Service URL: https://hub-financeiro-xxx.run.app
```

#### 5. Gerenciar Secrets
```bash
# Criar secret no Secret Manager
echo -n "xxx" | gcloud secrets create shopee-api-key --data-file=-

# Dar acesso a Cloud Run
gcloud secrets add-iam-policy-binding shopee-api-key \
  --member=serviceAccount:hub-financeiro@appspot.gserviceaccount.com \
  --role=roles/secretmanager.secretAccessor

# Usar em Cloud Run (via env var)
gcloud run deploy hub-financeiro \
  --set-cloudsql-instances=... \
  --set-env-vars="SHOPEE_API_KEY=projects/HUB-FINANCEIRO/secrets/shopee-api-key"
```

#### 6. Deployment via GitHub Actions
```bash
# .github/workflows/gcp-deploy.yml
name: Deploy to Google Cloud Run

on:
  push:
    branches: [master]

env:
  PROJECT_ID: hub-financeiro
  SERVICE_NAME: hub-financeiro
  REGION: us-central1

jobs:
  deploy:
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Setup Cloud SDK
        uses: google-github-actions/setup-gcloud@v1
        with:
          project_id: ${{ env.PROJECT_ID }}
          service_account_key: ${{ secrets.GCP_SA_KEY }}
          export_default_credentials: true
      
      - name: Build and Push Docker
        run: |
          gcloud builds submit \
            --tag gcr.io/${{ env.PROJECT_ID }}/${{ env.SERVICE_NAME }}:${{ github.sha }}
      
      - name: Deploy to Cloud Run
        run: |
          gcloud run deploy ${{ env.SERVICE_NAME }} \
            --image gcr.io/${{ env.PROJECT_ID }}/${{ env.SERVICE_NAME }}:${{ github.sha }} \
            --platform managed \
            --region ${{ env.REGION }} \
            --allow-unauthenticated
```

#### 7. Monitorar
```bash
# Ver logs
gcloud run services describe hub-financeiro \
  --region us-central1 \
  --format='value(status.url)'

# Cloud Logging
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=hub-financeiro" \
  --limit 50

# Métricas
gcloud monitoring metrics-descriptors list --filter="metric.type:run.googleapis.com/*"
```

### Estimativa de Custos GCP
- **Cloud Run**: $0.00001667 por vCPU-segundo (muito barato em baixo uso)
- **Memory**: $0.0000042 por GB-segundo
- **Requests**: $0.40 por 1M requests
- **Exemplo (100 requisições/dia, 512Mi, 5s cada)**:
  - Compute: ~$15/mês
  - Requests: ~$1.20/mês
- **Total**: ~$20-40/mês (muito variável por uso)

---

## OPÇÃO 4: DOCKER COMPOSE (LOCAL/VPS)

### Descrição
Deploy local ou em VPS próprio usando Docker Compose para desenvolvimento e produção.

### Arquitetura
```
nginx (Reverse Proxy)
    ├─ Streamlit (Port 8501)
    ├─ PostgreSQL (Data)
    └─ Redis (Cache)
```

### docker-compose.yml
```yaml
version: '3.8'

services:
  streamlit:
    build: .
    ports:
      - "8501:8501"
    environment:
      - SHOPEE_API_KEY=${SHOPEE_API_KEY}
      - TINY_API_TOKEN=${TINY_API_TOKEN}
      - ENVIRONMENT=production
      - LOG_LEVEL=INFO
    volumes:
      - ./logs:/app/logs
      - ./data:/app/data
    depends_on:
      - postgres
      - redis
    networks:
      - hub-network
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8501"]
      interval: 30s
      timeout: 10s
      retries: 3

  postgres:
    image: postgres:15-alpine
    environment:
      POSTGRES_DB: hub_financeiro
      POSTGRES_USER: hub_user
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
    networks:
      - hub-network
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    networks:
      - hub-network
    restart: unless-stopped

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - ./ssl:/etc/nginx/ssl:ro
    depends_on:
      - streamlit
    networks:
      - hub-network
    restart: unless-stopped

volumes:
  postgres_data:

networks:
  hub-network:
    driver: bridge
```

### nginx.conf (Reverse Proxy)
```nginx
upstream streamlit {
    server streamlit:8501;
}

server {
    listen 80;
    server_name hub-financeiro.example.com;
    
    # Redirect HTTP to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name hub-financeiro.example.com;
    
    ssl_certificate /etc/nginx/ssl/cert.pem;
    ssl_certificate_key /etc/nginx/ssl/key.pem;
    
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    
    # Gzip compression
    gzip on;
    gzip_types text/plain text/css application/json;
    
    location / {
        proxy_pass http://streamlit;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 86400;
    }
    
    # Health check endpoint
    location /health {
        return 200 "healthy\n";
        add_header Content-Type text/plain;
    }
}
```

### Deploy
```bash
# Criar .env
cat > .env << 'EOF'
SHOPEE_API_KEY=xxx
TINY_API_TOKEN=yyy
DB_PASSWORD=strong_password
ENVIRONMENT=production
EOF

# Iniciar services
docker-compose up -d

# Ver logs
docker-compose logs -f streamlit

# Stop
docker-compose down
```

### Custos VPS
- **DigitalOcean App Platform**: $12-25/mês
- **Linode**: $5-20/mês
- **Heroku**: Descontinuado
- **Render**: $7-25/mês

---

## COMPARATIVO DE PLATAFORMAS

| Aspecto | AWS | Azure | GCP | VPS |
|--------|-----|-------|-----|-----|
| **Setup** | Médio | Médio | Fácil | Fácil |
| **Custo Mín** | $30/mês | $110/mês | $20/mês | $5/mês |
| **Auto-scaling** | Sim | Sim | Sim | Manual |
| **Serverless** | Não | Não | Sim | Não |
| **Monitoramento** | CloudWatch | App Insights | Cloud Logging | Manual |
| **Suporte** | Excelente | Excelente | Bom | Comunidade |
| **Curva Aprendizado** | Alta | Média | Média | Baixa |

---

## CHECKLIST PRÉ-DEPLOYMENT

- [ ] Todos os testes passando (pytest -q)
- [ ] requirements.txt atualizado e congelado (pip freeze)
- [ ] Variáveis de ambiente documentadas
- [ ] Secrets armazenados em Secrets Manager
- [ ] GitHub Actions workflows configurados
- [ ] Dockerfile buildável e testado
- [ ] Health checks implementados
- [ ] Logs configurados e monitorados
- [ ] SSL/TLS certificados válidos
- [ ] Database backups automáticos
- [ ] Auto-scaling policies definidas
- [ ] Alertas configurados para erros

---

## PRÓXIMAS ETAPAS

1. **Escolher plataforma** baseado em:
   - Orçamento disponível
   - Expertise da equipe
   - Requisitos de escala
   - Preferências de vendor lock-in

2. **Preparar credenciais**:
   - Criar contas nas plataformas selecionadas
   - Gerar API keys
   - Configurar roles/permissions

3. **Testar deployment**:
   - Deploy em staging primeiro
   - Validar com dados reais
   - Monitore por 24-48 horas

4. **Configurar CI/CD**:
   - GitHub Actions workflows
   - Automated testing
   - Automated deployment

5. **Monitorar em produção**:
   - Setup alertas
   - Configure logging centralizado
   - Prepare runbook para incidents

---

## SUPORTE E RECURSOS

- **AWS Docs**: https://docs.aws.amazon.com/elasticbeanstalk/
- **Azure Docs**: https://docs.microsoft.com/en-us/azure/app-service/
- **GCP Docs**: https://cloud.google.com/run/docs
- **Streamlit Deployment**: https://docs.streamlit.io/library/get-started/installation
- **Docker**: https://docs.docker.com/

---

**Último Update**: 2024
**Version**: 1.0
