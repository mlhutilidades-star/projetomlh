#!/bin/bash

# Docker Compose Deployment Script (Local/VPS)
# Usage: ./deploy_docker.sh

set -e

VERSION=$(date +%Y%m%d-%H%M%S)
COMPOSE_FILE="docker-compose.yml"

echo "🚀 Iniciando deployment com Docker Compose..."
echo "   Version: $VERSION"

# 1. Validar Docker
echo "✓ Validando Docker..."
if ! command -v docker &> /dev/null; then
    echo "❌ Erro: Docker não instalado"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Erro: Docker Compose não instalado"
    exit 1
fi

# 2. Validar testes
echo "✓ Executando testes..."
python -m pytest tests/ -q --tb=no || exit 1

# 3. Validar arquivo .env
echo "✓ Validando arquivo .env..."
if [ ! -f .env ]; then
    echo "❌ Erro: Arquivo .env não encontrado"
    echo "   Crie um arquivo .env com as variáveis necessárias:"
    echo "   SHOPEE_API_KEY=xxx"
    echo "   TINY_API_TOKEN=yyy"
    echo "   DB_PASSWORD=zzz"
    exit 1
fi

# 4. Criar diretórios necessários
echo "✓ Preparando diretórios..."
mkdir -p logs data ssl

# 5. Parar containers antigos
echo "✓ Parando containers antigos..."
docker-compose down --remove-orphans 2>/dev/null || true

# 6. Remover imagens antigas
echo "✓ Limpando imagens antigas..."
docker image prune -f --filter "dangling=true" 2>/dev/null || true

# 7. Build images
echo "✓ Building Docker images..."
docker-compose build --no-cache

# 8. Iniciar containers
echo "✓ Iniciando containers..."
docker-compose up -d

# 9. Aguardar services
echo "✓ Aguardando services iniciar..."
sleep 10

# 10. Verificar status
echo "✓ Verificando status dos containers..."
docker-compose ps

# 11. Executar health checks
echo "✓ Executando health checks..."

# Check Streamlit
echo "  - Streamlit..."
if docker-compose exec -T streamlit curl -f http://localhost:8501 > /dev/null 2>&1; then
    echo "    ✅ Streamlit está saudável"
else
    echo "    ⚠️  Streamlit pode não estar pronto ainda"
fi

# Check PostgreSQL
echo "  - PostgreSQL..."
if docker-compose exec -T postgres pg_isready -U hub_user > /dev/null 2>&1; then
    echo "    ✅ PostgreSQL está saudável"
else
    echo "    ❌ PostgreSQL não respondeu"
fi

# Check Redis
echo "  - Redis..."
if docker-compose exec -T redis redis-cli ping > /dev/null 2>&1; then
    echo "    ✅ Redis está saudável"
else
    echo "    ❌ Redis não respondeu"
fi

# 12. Ver logs recentes
echo ""
echo "✓ Últimos logs do Streamlit:"
docker-compose logs --tail=20 streamlit

# 13. Criar snapshot
echo ""
echo "✓ Criando snapshot..."
docker-compose exec -T postgres pg_dump -U hub_user hub_financeiro > backups/backup-$VERSION.sql 2>/dev/null || true

# 14. Iniciar monitoramento background
echo ""
echo "✓ Iniciando monitoramento..."
# Script simples de monitoramento
cat > .monitor.sh << 'EOF'
#!/bin/bash
while true; do
    echo "[$(date)] Verificando status..."
    docker-compose ps
    
    # Verificar uso de recursos
    echo "CPU/Memory:"
    docker stats --no-stream
    
    sleep 60
done
EOF

chmod +x .monitor.sh

echo "🎉 Deployment concluído!"
echo ""
echo "📍 URLs de acesso:"
echo "   Streamlit: http://localhost:8501"
echo "   PostgreSQL: localhost:5432"
echo "   Redis: localhost:6379"
echo ""
echo "📊 Comandos úteis:"
echo "   Ver logs:        docker-compose logs -f streamlit"
echo "   Parar:           docker-compose down"
echo "   Reiniciar:       docker-compose restart"
echo "   Shell:           docker-compose exec streamlit bash"
echo "   Backup BD:       docker-compose exec postgres pg_dump -U hub_user hub_financeiro > backup.sql"
echo ""
echo "🔐 Backup:"
echo "   Backups automáticos: backups/backup-$VERSION.sql"
echo ""
echo "⚠️  Produção:"
echo "   Para produção com nginx/SSL, configure o nginx.conf"
echo "   E execute: docker-compose -f docker-compose.prod.yml up -d"
