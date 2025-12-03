Param(
  [string]$Name = "shopee-oauth"
)

# Inicia um Cloudflare Named Tunnel previamente criado
# Requer: cloudflared autenticado e túnel $Name criado e roteado a um domínio

Write-Host "Iniciando Named Tunnel: $Name" -ForegroundColor Cyan

# Dica: Se o cloudflared não estiver no PATH, ajuste a linha abaixo
$cloudflared = "cloudflared"

& $cloudflared tunnel run $Name