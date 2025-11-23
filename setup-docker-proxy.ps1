# Script para configurar proxy de Bright Data a nivel de Docker (PowerShell)
# Uso: .\setup-docker-proxy.ps1

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Configuración de Proxy para Docker (Windows)" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

# Leer configuración desde .env
$envContent = @{}
if (Test-Path ".env") {
    Get-Content ".env" | ForEach-Object {
        if ($_ -match '^\s*([^#][^=]+)=(.*)$') {
            $key = $matches[1].Trim()
            $value = $matches[2].Trim()
            $envContent[$key] = $value
        }
    }
}

$PROXY_HOST = if ($envContent["SIASCAFE_PROXY_HOST"]) { $envContent["SIASCAFE_PROXY_HOST"] } else { "brd.superproxy.io" }
$PROXY_PORT = if ($envContent["SIASCAFE_PROXY_PORT"]) { $envContent["SIASCAFE_PROXY_PORT"] } else { "33335" }
$PROXY_USER = if ($envContent["SIASCAFE_PROXY_USER"]) { $envContent["SIASCAFE_PROXY_USER"] } else { "brd-customer-hl_6ad5dde5-zone-datacenter_proxy1" }
$PROXY_PASS = if ($envContent["SIASCAFE_PROXY_PASS"]) { $envContent["SIASCAFE_PROXY_PASS"] } else { "vekb114yzhdx" }
$PROXY_COUNTRY = if ($envContent["SIASCAFE_PROXY_COUNTRY"]) { $envContent["SIASCAFE_PROXY_COUNTRY"] } else { "CO" }

# Construir username con país
if ($PROXY_COUNTRY -and $PROXY_USER -notmatch "-country-$PROXY_COUNTRY") {
    $PROXY_USER = "${PROXY_USER}-country-${PROXY_COUNTRY}"
}

# Construir URL del proxy
$PROXY_URL = "http://${PROXY_USER}:${PROXY_PASS}@${PROXY_HOST}:${PROXY_PORT}"

Write-Host "[INFO] Configuración del proxy:" -ForegroundColor Yellow
Write-Host "  Host: $PROXY_HOST" -ForegroundColor White
Write-Host "  Port: $PROXY_PORT" -ForegroundColor White
Write-Host "  User: $PROXY_USER" -ForegroundColor White
Write-Host "  Country: $PROXY_COUNTRY" -ForegroundColor White
Write-Host ""

# Configurar proxy para Docker Desktop (settings.json) - Proxy transparente
Write-Host "[1] Configurando proxy para Docker Desktop (transparente para contenedores)..." -ForegroundColor Yellow
Write-Host "  El proxy será transparente para todos los contenedores" -ForegroundColor Gray
Write-Host ""

# Configurar proxy en Docker Desktop (settings.json)
Write-Host "[3] Configurando proxy en Docker Desktop..." -ForegroundColor Yellow

$DOCKER_SETTINGS_FILE = "$env:APPDATA\Docker\settings.json"

if (Test-Path $DOCKER_SETTINGS_FILE) {
    Write-Host "  Archivo settings.json encontrado, actualizando..." -ForegroundColor Gray
    try {
        $settings = Get-Content $DOCKER_SETTINGS_FILE -Raw | ConvertFrom-Json
        
        # Agregar configuración de proxy si no existe
        if (-not $settings.PSObject.Properties.Name -contains "proxies") {
            $settings | Add-Member -MemberType NoteProperty -Name "proxies" -Value @{}
        }
        
        $settings.proxies.httpProxy = $PROXY_URL
        $settings.proxies.httpsProxy = $PROXY_URL
        $settings.proxies.noProxy = "localhost,127.0.0.1,::1,*.local"
        $settings.proxies.exclude = ""
        
        $settings | ConvertTo-Json -Depth 10 | Set-Content $DOCKER_SETTINGS_FILE -Encoding UTF8
        Write-Host "  [OK] Settings.json actualizado" -ForegroundColor Green
        Write-Host "  NOTA: Reinicia Docker Desktop para aplicar los cambios" -ForegroundColor Yellow
    } catch {
        Write-Host "  [WARN] No se pudo actualizar settings.json: $_" -ForegroundColor Yellow
        Write-Host "  Puedes configurarlo manualmente en Docker Desktop > Settings > Resources > Proxies" -ForegroundColor Gray
    }
} else {
    Write-Host "  [INFO] Settings.json no encontrado (Docker Desktop puede no estar instalado)" -ForegroundColor Gray
    Write-Host "  Configura el proxy manualmente en Docker Desktop si es necesario" -ForegroundColor Gray
}

Write-Host ""
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "[OK] Configuración completada" -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "El proxy está configurado a nivel de Docker Desktop." -ForegroundColor White
Write-Host "Todos los contenedores usarán el proxy automáticamente." -ForegroundColor White
Write-Host ""
Write-Host "Ventajas de esta configuración:" -ForegroundColor Yellow
Write-Host "  - Proxy transparente (no requiere configuración en contenedores)" -ForegroundColor Gray
Write-Host "  - Evita problemas de autenticación" -ForegroundColor Gray
Write-Host "  - Funciona para todo el tráfico de red" -ForegroundColor Gray
Write-Host ""
Write-Host "Para verificar:" -ForegroundColor Yellow
Write-Host "  docker run --rm alpine/curl curl -s https://api.ipify.org" -ForegroundColor White
Write-Host ""
Write-Host "IMPORTANTE:" -ForegroundColor Yellow
Write-Host "  1. Reinicia Docker Desktop después de ejecutar este script" -ForegroundColor White
Write-Host "  2. Los contenedores existentes necesitan ser recreados para usar el proxy" -ForegroundColor White
Write-Host ""

