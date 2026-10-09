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
    $proc = Start-Process -FilePath $cfExe -ArgumentList "tunnel --url http://localhost:$($svc.Port)" -RedirectStandardError $logFile -WindowStyle Hidden -PassThru
    $processes += $proc

    # Esperar URL en logs (hasta 15 seg)
    $url = $null
    $startWait = Get-Date
    while (-not $url -and ((Get-Date) - $startWait).TotalSeconds -lt 15) {
        Start-Sleep -Milliseconds 500
        if (Test-Path $logFile) {
            $content = Get-Content $logFile -Raw -ErrorAction SilentlyContinue
            if ($content -match "https://[a-zA-Z0-9-]+\.trycloudflare\.com") {
                $url = $matches[0]
                break
            }
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
        $raw = [System.IO.File]::ReadAllText($grafanaJsonPath)
        $jsonContent = $raw | ConvertFrom-Json
        foreach ($key in $urls.Keys) {
            $jsonContent.$key = $urls[$key]
        }
        $jsonOut = $jsonContent | ConvertTo-Json -Depth 5
        [System.IO.File]::WriteAllText($grafanaJsonPath, $jsonOut, [System.Text.UTF8Encoding]::new($false))
        Write-Host "`n[OK] presentacion/grafana.json actualizado con las nuevas URLs (UTF-8 sin BOM)." -ForegroundColor Green
    } catch {
        Write-Warning "No se pudo actualizar presentacion/grafana.json: $_"
    }
}

Write-Host "`nTuneles activos en segundo plano." -ForegroundColor Cyan
