#!/bin/bash

# AWS Elastic Beanstalk Deployment Script
# Usage: ./deploy_aws.sh <environment> <region>

set -e

ENVIRONMENT=${1:-staging}
REGION=${2:-us-east-1}
APP_NAME="hub-financeiro"
VERSION=$(date +%Y%m%d-%H%M%S)

echo "🚀 Iniciando deployment para AWS Elastic Beanstalk..."
echo "   Environment: $ENVIRONMENT"
echo "   Region: $REGION"
echo "   Version: $VERSION"

# 1. Validar testes
echo "✓ Executando testes..."
python -m pytest tests/ -q --tb=no || exit 1

# 2. Validar requirements.txt
echo "✓ Validando requirements.txt..."
pip check || echo "⚠️  Aviso: Possíveis conflitos de dependência"

# 3. Validar variáveis de ambiente
echo "✓ Validando variáveis de ambiente..."
required_vars=("SHOPEE_API_KEY" "TINY_API_TOKEN" "ENVIRONMENT")
for var in "${required_vars[@]}"; do
    if [ -z "${!var}" ]; then
        echo "❌ Erro: Variável $var não definida"
        exit 1
    fi
done

# 4. Build Docker (opcional)
if [ "$BUILD_DOCKER" = "true" ]; then
    echo "✓ Building Docker image..."
    docker build -t hub-financeiro:$VERSION .
    docker tag hub-financeiro:$VERSION hub-financeiro:latest
fi

# 5. Criar ZIP para EB
echo "✓ Preparando pacote EB..."
rm -f hub-financeiro-$VERSION.zip
zip -r hub-financeiro-$VERSION.zip . \
    -x "*.git*" "*.pyc" "__pycache__/*" "*.egg-info/*" "node_modules/*" \
    -x "tests/*" ".pytest_cache/*" "*.venv/*"

# 6. Upload para S3
echo "✓ Upload para S3..."
aws s3 cp hub-financeiro-$VERSION.zip s3://hub-financeiro-deployments/$ENVIRONMENT/

# 7. Deploy
echo "✓ Enviando para Elastic Beanstalk..."
aws elasticbeanstalk create-app-version \
    --application-name $APP_NAME \
    --version-label $VERSION \
    --source-bundle S3Bucket=hub-financeiro-deployments,S3Key=$ENVIRONMENT/hub-financeiro-$VERSION.zip \
    --region $REGION

# 8. Atualizar ambiente
echo "✓ Atualizando ambiente EB..."
aws elasticbeanstalk update-environment \
    --application-name $APP_NAME \
    --environment-name $ENVIRONMENT-env \
    --version-label $VERSION \
    --region $REGION

# 9. Monitor deployment
echo "✓ Monitorando deployment..."
for i in {1..60}; do
    STATUS=$(aws elasticbeanstalk describe-environments \
        --application-name $APP_NAME \
        --environment-name $ENVIRONMENT-env \
        --region $REGION \
        --query 'Environments[0].Status' \
        --output text)
    
    if [ "$STATUS" = "Ready" ]; then
        echo "✅ Deployment bem-sucedido!"
        break
    elif [ "$STATUS" = "Terminated" ]; then
        echo "❌ Deployment falhou - Ambiente foi terminado"
        exit 1
    fi
    
    echo "   Status: $STATUS (aguardando...)"
    sleep 10
done

# 10. Testar health check
echo "✓ Testando health check..."
URL=$(aws elasticbeanstalk describe-environments \
    --application-name $APP_NAME \
    --environment-name $ENVIRONMENT-env \
    --region $REGION \
    --query 'Environments[0].CNAME' \
    --output text)

sleep 5
curl -f http://$URL/health || echo "⚠️  Health check falhou"

# 11. Limpar
rm -f hub-financeiro-$VERSION.zip

echo "🎉 Deployment concluído!"
echo "   URL: http://$URL"
echo "   Versão: $VERSION"
