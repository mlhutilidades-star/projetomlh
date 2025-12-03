# Monitor de Agente Autônomo - PowerShell
# Monitora TODO e STATUS, dispara Aider automaticamente

param(
    [int]$Interval = 2,
    [int]$CooldownSeconds = 60
)

# Configuração
$TodoFile = "..\PROJETO MLH\docs\TODO_AUTONOMO_MLH.md"
$StatusFile = "..\PROJETO MLH\docs\STATUS_AUTONOMO.md"
$StateFile = "agent_monitor_state.json"
$LogFile = "logs\auto_agent.log"

# Criar diretório de logs se não existir
if (-not (Test-Path "logs")) {
    New-Item -ItemType Directory -Path "logs" | Out-Null
}

# Função de log
function Write-Log {
    param(
        [string]$Message,
        [string]$Level = "INFO"
    )
    
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $logLine = "[$timestamp] [$Level] $Message"
    
    Add-Content -Path $LogFile -Value $logLine
    Write-Host "[$Level] $Message"
}

# Função para carregar estado
function Load-State {
    if (Test-Path $StateFile) {
        try {
            return Get-Content $StateFile | ConvertFrom-Json -AsHashtable
        } catch {
            Write-Log "Erro ao carregar estado: $_" "WARN"
            return @{}
        }
    }
    return @{}
}

# Função para salvar estado
function Save-State {
    param([hashtable]$State)
    
    try {
        $State | ConvertTo-Json | Set-Content $StateFile
    } catch {
        Write-Log "Falha ao salvar estado: $_" "ERROR"
    }
}

# Função para calcular hash do arquivo
function Get-FileHashMD5 {
    param([string]$FilePath)
    
    if (-not (Test-Path $FilePath)) {
        return $null
    }
    
    try {
        $hash = Get-FileHash -Path $FilePath -Algorithm MD5
        return $hash.Hash
    } catch {
        Write-Log "Falha ao calcular hash de ${FilePath}: $_" "ERROR"
        return $null
    }
}

# Função para verificar atualizações
function Check-ForUpdates {
    param([hashtable]$State)
    
    $updated = $false
    
    # Verifica TODO
    if (Test-Path $TodoFile) {
        $todoHash = Get-FileHashMD5 -FilePath $TodoFile
        if ($todoHash -and $todoHash -ne $State['todo_hash']) {
            Write-Log "Atualização detectada em TODO_AUTONOMO_MLH.md" "INFO"
            $State['todo_hash'] = $todoHash
            $updated = $true
        }
    }
    
    # Verifica STATUS
    if (Test-Path $StatusFile) {
        $statusHash = Get-FileHashMD5 -FilePath $StatusFile
        if ($statusHash -and $statusHash -ne $State['status_hash']) {
            Write-Log "Atualização detectada em STATUS_AUTONOMO.md" "INFO"
            $State['status_hash'] = $statusHash
            $updated = $true
        }
    }
    
    return $updated
}

# Função para verificar se deve executar Aider
function Should-RunAider {
    param([hashtable]$State)
    
    $lastRun = $State['last_aider_run']
    if (-not $lastRun) {
        return $true
    }
    
    $lastRunTime = [DateTime]::Parse($lastRun)
    $elapsed = (Get-Date) - $lastRunTime
    
    if ($elapsed.TotalSeconds -lt $CooldownSeconds) {
        Write-Log "Aider executado recentemente, aguardando cooldown ($([int]$elapsed.TotalSeconds)s / ${CooldownSeconds}s)" "INFO"
        return $false
    }
    
    return $true
}

# Função para executar Aider
function Start-Aider {
    param([hashtable]$State)
    
    if (-not (Should-RunAider -State $State)) {
        return
    }
    
    Write-Log "Iniciando Aider em modo automático" "INFO"
    
    try {
        $aiderCmd = "aider --model gpt-4o --yes --auto-commits --watch-files ."
        Write-Log "Comando: $aiderCmd" "INFO"
        
        # Inicia Aider em janela separada
        Start-Process powershell -ArgumentList "-NoExit", "-Command", "& '.venv-aider\Scripts\Activate.ps1'; $aiderCmd" -WindowStyle Normal
        
        # Atualiza timestamp
        $State['last_aider_run'] = (Get-Date).ToString("o")
        Save-State -State $State
        
        Write-Log "Aider iniciado com sucesso" "INFO"
    } catch {
        Write-Log "Erro ao executar Aider: $_" "ERROR"
    }
}

# Main
Write-Log "Monitor de agente autônomo iniciado" "INFO"
Write-Log "Monitorando: TODO_AUTONOMO_MLH.md e STATUS_AUTONOMO.md" "INFO"
Write-Log "Verificando a cada $Interval segundos" "INFO"
Write-Log "Cooldown entre execuções: $CooldownSeconds segundos" "INFO"
Write-Log "Logs em: $LogFile" "INFO"

Write-Host "`nMonitor de agente autonomo ativo" -ForegroundColor Cyan
Write-Host "Pressione Ctrl+C para parar`n" -ForegroundColor Yellow

$state = Load-State

# Inicializa hashes se não existirem
if (Test-Path $TodoFile) {
    if (-not $state['todo_hash']) {
        $state['todo_hash'] = Get-FileHashMD5 -FilePath $TodoFile
    }
}

if (Test-Path $StatusFile) {
    if (-not $state['status_hash']) {
        $state['status_hash'] = Get-FileHashMD5 -FilePath $StatusFile
    }
}

Save-State -State $state

# Loop de monitoramento
try {
    while ($true) {
        Start-Sleep -Seconds $Interval
        
        # Verifica atualizações
        if (Check-ForUpdates -State $state) {
            Write-Log "Mudanças detectadas, avaliando execução do Aider" "INFO"
            Start-Aider -State $state
            Save-State -State $state
        }
    }
} catch {
    Write-Log "Monitor interrompido: $_" "INFO"
    Write-Host "`nMonitor de agente encerrado" -ForegroundColor Green
}
