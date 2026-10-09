<#
.SYNOPSIS
  Inicia los túneles seguros de Cloudflare para HaizeLab y sincroniza presentacion/grafana.json.
.DESCRIPTION
  Levanta túneles efímeros de Cloudflare para:
    - Grafana (3000)
    - InfluxDB Proxy (8085)
    - Node-RED (1880)
    - Chatbot Assistant (8000)
  Captura las URLs generadas (*.trycloudflare.com) y actualiza automáticamente presentacion/grafana.json.
#>

param(
    [switch]$Help
)

if ($Help) {
    Write-Host "Uso: .\scripts\iniciar_tuneles.ps1"
    Write-Host "Requiere: cloudflared instalado y servicios Docker en ejecucion."
    exit 0
}

Write-Host "=== HaizeLab - Lanzador de Tuneles Cloudflare ===" -ForegroundColor Cyan

# Localizar binario de cloudflared
$cfExe = $null
if (Get-Command cloudflared -ErrorAction SilentlyContinue) {
    $cfExe = "cloudflared"
} elseif (Test-Path "C:\Program Files (x86)\cloudflared\cloudflared.exe") {
    $cfExe = "C:\Program Files (x86)\cloudflared\cloudflared.exe"
} elseif (Test-Path "C:\Program Files\cloudflared\cloudflared.exe") {
    $cfExe = "C:\Program Files\cloudflared\cloudflared.exe"
} else {
    Write-Error "No se encontro cloudflared en PATH ni en Program Files. Instálalo con 'winget install --id Cloudflare.cloudflared'."
    exit 1
}

$tmpDir = Join-Path $env:TEMP "haizelab_tunnels"
if (-not (Test-Path $tmpDir)) {
    New-Item -ItemType Directory -Path $tmpDir -Force | Out-Null
}

$services = @(
    @{ Name = "base"; Port = 3000; Label = "Grafana" },
    @{ Name = "influx"; Port = 8085; Label = "Influx Proxy" },
    @{ Name = "nodered"; Port = 1880; Label = "Node-RED" },
    @{ Name = "chatbot"; Port = 8000; Label = "Chatbot API" }
)

$urls = @{}
$processes = @()

foreach ($svc in $services) {
    $logFile = Join-Path $tmpDir "$($svc.Name).log"
    if (Test-Path $logFile) { Remove-Item $logFile -Force }

    Write-Host "Iniciando tunel para $($svc.Label) (puerto $($svc.Port))..." -ForegroundColor Yellow
    $psi = New-Object System.Diagnostics.ProcessStartInfo
    $psi.FileName = $cfExe
    $psi.Arguments = "tunnel --url http://localhost:$($svc.Port)"
    $psi.RedirectStandardError = $true
    $psi.RedirectStandardOutput = $true
    $psi.UseShellExecute = $false
    $psi.CreateNoWindow = $true

    $proc = [System.Diagnostics.Process]::Start($psi)
    $processes += $proc

    # Esperar URL en logs (hasta 15 seg)
    $url = $null
    $startWait = Get-Date
    while (-not $url -and ((Get-Date) - $startWait).TotalSeconds -lt 15) {
        Start-Sleep -Milliseconds 500
        $errLine = $proc.StandardError.ReadLine()
        while ($errLine) {
            Add-Content -Path $logFile -Value $errLine
            if ($errLine -match "https://[a-zA-Z0-9-]+\.trycloudflare\.com") {
                $url = $matches[0]
                break
            }
            if ($proc.StandardError.EndOfStream) { break }
            $errLine = $proc.StandardError.ReadLine()
        }
    }

    if ($url) {
        $urls[$svc.Name] = $url
        Write-Host "  -> $($svc.Label): $url" -ForegroundColor Green
    } else {
        Write-Warning "No se pudo extraer URL para $($svc.Label) en el tiempo esperado. Revisa $logFile."
    }
}

# Actualizar presentacion/grafana.json si tenemos URLs
$grafanaJsonPath = Join-Path $PSScriptRoot "..\presentacion\grafana.json"
if (Test-Path $grafanaJsonPath) {
    try {
        $jsonContent = Get-Content $grafanaJsonPath -Raw | ConvertFrom-Json
        foreach ($key in $urls.Keys) {
            $jsonContent.$key = $urls[$key]
        }
        $jsonContent | ConvertTo-Json -Depth 5 | Set-Content $grafanaJsonPath -Encoding utf8
        Write-Host "`n[OK] presentacion/grafana.json actualizado con las nuevas URLs." -ForegroundColor Green
    } catch {
        Write-Warning "No se pudo actualizar presentacion/grafana.json: $_"
    }
}

Write-Host "`nTuneles activos en segundo plano." -ForegroundColor Cyan
