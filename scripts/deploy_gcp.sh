#!/bin/bash

# Google Cloud Run Deployment Script
# Usage: ./deploy_gcp.sh <project-id> <service-name>

set -e

PROJECT_ID=${1:-hub-financeiro}
SERVICE_NAME=${2:-hub-financeiro}
REGION=${3:-us-central1}
VERSION=$(date +%Y%m%d-%H%M%S)

echo "🚀 Iniciando deployment para Google Cloud Run..."
echo "   Project ID: $PROJECT_ID"
echo "   Service: $SERVICE_NAME"
echo "   Region: $REGION"
echo "   Version: $VERSION"

# 1. Validar testes
echo "✓ Executando testes..."
python -m pytest tests/ -q --tb=no || exit 1

# 2. Validar gcloud CLI
echo "✓ Validando Google Cloud SDK..."
if ! command -v gcloud &> /dev/null; then
    echo "❌ Erro: Google Cloud SDK não instalado"
    exit 1
fi

# 3. Autenticar
echo "✓ Autenticando no Google Cloud..."
gcloud config set project $PROJECT_ID

# 4. Validar projeto
echo "✓ Validando projeto..."
if ! gcloud projects describe $PROJECT_ID > /dev/null 2>&1; then
    echo "❌ Erro: Projeto '$PROJECT_ID' não existe"
    exit 1
fi

# 5. Build Docker
echo "✓ Building Docker image..."
docker build -t gcr.io/$PROJECT_ID/$SERVICE_NAME:$VERSION . || exit 1
docker tag gcr.io/$PROJECT_ID/$SERVICE_NAME:$VERSION gcr.io/$PROJECT_ID/$SERVICE_NAME:latest

# 6. Autenticar Docker
echo "✓ Autenticando Docker com GCR..."
gcloud auth configure-docker

# 7. Push para Container Registry
echo "✓ Enviando image para Google Container Registry..."
docker push gcr.io/$PROJECT_ID/$SERVICE_NAME:$VERSION || exit 1
docker push gcr.io/$PROJECT_ID/$SERVICE_NAME:latest

# 8. Deploy para Cloud Run
echo "✓ Deployando para Cloud Run..."
gcloud run deploy $SERVICE_NAME \
    --image gcr.io/$PROJECT_ID/$SERVICE_NAME:$VERSION \
    --platform managed \
    --region $REGION \
    --memory 512Mi \
    --cpu 1 \
    --timeout 3600 \
    --max-instances 10 \
    --min-instances 1 \
    --allow-unauthenticated \
    --set-env-vars="ENVIRONMENT=production,LOG_LEVEL=INFO" \
    --no-traffic

# 9. Verificar deployment
echo "✓ Obtendo URL do serviço..."
SERVICE_URL=$(gcloud run services describe $SERVICE_NAME \
    --platform managed \
    --region $REGION \
    --format 'value(status.url)')

echo "✓ Aguardando serviço ficar pronto..."
sleep 5

# 10. Testar health check
echo "✓ Testando health check..."
if curl -s -f $SERVICE_URL/health > /dev/null 2>&1; then
    echo "✅ Health check passou!"
else
    echo "⚠️  Health check falhou, verifique os logs"
fi

# 11. Migrar tráfego (100%)
echo "✓ Migrando tráfego para nova versão..."
gcloud run services update-traffic $SERVICE_NAME \
    --to-latest \
    --region $REGION \
    --platform managed

# 12. Ver logs
echo "✓ Últimos logs:"
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=$SERVICE_NAME" \
    --limit 10 \
    --format json | jq '.[] | {timestamp: .timestamp, message: .textPayload}'

# 13. Informações de monitoramento
echo ""
echo "📊 Monitorar com:"
echo "   gcloud logging read \"resource.type=cloud_run_revision AND resource.labels.service_name=$SERVICE_NAME\" --limit 50"
echo ""

echo "🎉 Deployment concluído!"
echo "   URL: $SERVICE_URL"
echo "   Versão: $VERSION"
echo "   Projeto: $PROJECT_ID"
echo ""
echo "Próximos passos:"
echo "  1. Testar em: $SERVICE_URL"
echo "  2. Ver logs: gcloud run logs read $SERVICE_NAME --region $REGION --limit 50"
echo "  3. Se algo deu errado, reverter com: gcloud run services describe $SERVICE_NAME --platform managed --region $REGION"
