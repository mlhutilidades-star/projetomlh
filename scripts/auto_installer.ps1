# Monitor de requirements.txt - PowerShell
# Detecta novos pacotes e instala automaticamente

param(
    [int]$Interval = 2
)

# Configuração
$RequirementsFile = "requirements.txt"
$StateFile = "installed_requirements.json"
$LogFile = "logs\auto_installer.log"

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
        Write-Log "Falha ao calcular hash: $_" "ERROR"
        return $null
    }
}

# Função para parsear linha de pacote
function Parse-PackageLine {
    param([string]$Line)
    
    $Line = $Line.Trim()
    
    # Ignorar linhas vazias e comentários
    if ([string]::IsNullOrWhiteSpace($Line) -or $Line.StartsWith('#')) {
        return $null
    }
    
    # Remover comentários inline
    if ($Line -contains '#') {
        $Line = ($Line -split '#')[0].Trim()
    }
    
    # Extrair nome do pacote
    $separators = @('==', '>=', '<=', '~=', '!=', '<', '>')
    foreach ($sep in $separators) {
        if ($Line -contains $sep) {
            $packageName = ($Line -split [regex]::Escape($sep))[0].Trim()
            return @{
                Name = $packageName
                Line = $Line
            }
        }
    }
    
    # Sem versão especificada
    return @{
        Name = $Line.Trim()
        Line = $Line.Trim()
    }
}

# Função para ler requirements
function Read-Requirements {
    if (-not (Test-Path $RequirementsFile)) {
        return @()
    }
    
    $packages = @()
    
    try {
        $lines = Get-Content $RequirementsFile
        $lineNum = 1
        
        foreach ($line in $lines) {
            $pkg = Parse-PackageLine -Line $line
            if ($pkg) {
                $packages += @{
                    Name = $pkg.Name
                    Line = $pkg.Line
                    LineNum = $lineNum
                }
            }
            $lineNum++
        }
    } catch {
        Write-Log "Falha ao ler requirements.txt: $_" "ERROR"
    }
    
    return $packages
}

# Função para instalar pacote
function Install-Package {
    param($PackageInfo)
    
    $packageLine = $PackageInfo.Line
    $packageName = $PackageInfo.Name
    
    Write-Log "Instalando: $packageLine" "INFO"
    
    try {
        $result = & python -m pip install $packageLine 2>&1
        
        if ($LASTEXITCODE -eq 0) {
            Write-Log "Pacote instalado com sucesso: $packageName" "INFO"
            return $true
        } else {
            Write-Log "Falha ao instalar ${packageName}: $result" "ERROR"
            return $false
        }
    } catch {
        Write-Log "Excecao ao instalar ${packageName}: $_" "ERROR"
        return $false
    }
}

# Função principal de verificação
function Check-AndInstall {
    param([hashtable]$InstalledPackages)
    
    $packages = Read-Requirements
    $changed = $false
    
    foreach ($pkg in $packages) {
        $pkgName = $pkg.Name
        $pkgLine = $pkg.Line
        
        # Verifica se já foi instalado
        if (-not $InstalledPackages.ContainsKey($pkgName) -or $InstalledPackages[$pkgName] -ne $pkgLine) {
            # Novo pacote ou versão diferente
            if (Install-Package -PackageInfo $pkg) {
                $InstalledPackages[$pkgName] = $pkgLine
                $changed = $true
            }
        }
    }
    
    if ($changed) {
        Save-State -State $InstalledPackages
    }
}

# Main
Write-Log "Sistema de auto-instalação iniciado" "INFO"
Write-Log "Monitorando: $RequirementsFile" "INFO"
Write-Log "Verificando a cada $Interval segundos" "INFO"
Write-Log "Logs em: $LogFile" "INFO"

Write-Host "`nMonitor de requirements.txt ativo" -ForegroundColor Cyan
Write-Host "Pressione Ctrl+C para parar`n" -ForegroundColor Yellow

$installedPackages = Load-State
$lastHash = Get-FileHashMD5 -FilePath $RequirementsFile

# Primeira verificação
Check-AndInstall -InstalledPackages $installedPackages

# Loop de monitoramento
try {
    while ($true) {
        Start-Sleep -Seconds $Interval
        
        $currentHash = Get-FileHashMD5 -FilePath $RequirementsFile
        
        if ($currentHash -ne $lastHash) {
            Write-Log "Alteração detectada em $RequirementsFile" "INFO"
            Check-AndInstall -InstalledPackages $installedPackages
            $lastHash = $currentHash
        }
    }
} catch {
    Write-Log "Monitor interrompido: $_" "INFO"
    Write-Host "`nMonitor encerrado. Pacotes gerenciados: $($installedPackages.Count)" -ForegroundColor Green
}
