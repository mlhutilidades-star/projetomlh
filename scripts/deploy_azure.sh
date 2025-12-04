#!/bin/bash

# Azure App Service Deployment Script
# Usage: ./deploy_azure.sh <resource-group> <app-name>

set -e

RESOURCE_GROUP=${1:-hub-financeiro-rg}
APP_NAME=${2:-hub-financeiro-app}
VERSION=$(date +%Y%m%d-%H%M%S)

echo "🚀 Iniciando deployment para Azure App Service..."
echo "   Resource Group: $RESOURCE_GROUP"
echo "   App Name: $APP_NAME"
echo "   Version: $VERSION"

# 1. Validar testes
echo "✓ Executando testes..."
python -m pytest tests/ -q --tb=no || exit 1

# 2. Validar Azure CLI
echo "✓ Validando Azure CLI..."
if ! command -v az &> /dev/null; then
    echo "❌ Erro: Azure CLI não instalado"
    exit 1
fi

# 3. Autenticar
echo "✓ Autenticando no Azure..."
az account show > /dev/null || az login

# 4. Validar resource group
echo "✓ Validando Resource Group..."
if ! az group exists --name $RESOURCE_GROUP --query value -o tsv | grep -q "true"; then
    echo "❌ Erro: Resource Group '$RESOURCE_GROUP' não existe"
    exit 1
fi

# 5. Build local
echo "✓ Preparando aplicação..."
rm -rf dist/
mkdir -p dist/

# Copiar arquivos necessários
cp -r . dist/ \
    --exclude=.git \
    --exclude=__pycache__ \
    --exclude=*.pyc \
    --exclude=.pytest_cache \
    --exclude=.venv \
    --exclude=tests

# 6. Criar zip
echo "✓ Comprimindo artefatos..."
cd dist
zip -r ../hub-financeiro-$VERSION.zip . -q
cd ..

# 7. Deploy via zip
echo "✓ Enviando para Azure App Service..."
az webapp deployment source config-zip \
    --resource-group $RESOURCE_GROUP \
    --name $APP_NAME \
    --src hub-financeiro-$VERSION.zip

# 8. Monitor deployment
echo "✓ Monitorando deployment..."
sleep 10

# 9. Verificar status
echo "✓ Verificando saúde da aplicação..."
URL=$(az webapp show \
    --resource-group $RESOURCE_GROUP \
    --name $APP_NAME \
    --query defaultHostName \
    --output tsv)

for i in {1..30}; do
    if curl -s -f https://$URL/health > /dev/null 2>&1; then
        echo "✅ Deployment bem-sucedido!"
        break
    fi
    echo "   Aguardando aplicação iniciar... ($i/30)"
    sleep 2
done

# 10. Ver logs
echo "✓ Últimos logs da aplicação:"
az webapp log tail \
    --resource-group $RESOURCE_GROUP \
    --name $APP_NAME \
    --lines 20

# 11. Limpar
rm -rf dist/ hub-financeiro-$VERSION.zip

echo "🎉 Deployment concluído!"
echo "   URL: https://$URL"
echo "   Versão: $VERSION"
echo ""
echo "Próximos passos:"
echo "  1. Testar a aplicação em: https://$URL"
echo "  2. Ver logs com: az webapp log tail --resource-group $RESOURCE_GROUP --name $APP_NAME"
echo "  3. Configurar domínio custom se necessário"
