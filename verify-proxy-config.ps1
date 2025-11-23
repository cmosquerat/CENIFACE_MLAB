# Script para verificar configuración de proxy (PowerShell)
# Uso: .\verify-proxy-config.ps1

$containerName = "multilab-agroanalitica"

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Verificación de Configuración de Proxy" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

# Verificar si el contenedor está corriendo
$containerStatus = docker ps --format "{{.Names}}" | Select-String -Pattern "^${containerName}$"
if (-not $containerStatus) {
    Write-Host "[ERROR] Contenedor ${containerName} no está corriendo" -ForegroundColor Red
    exit 1
}

Write-Host "[1] Verificando variables de entorno en el contenedor..." -ForegroundColor Yellow
Write-Host ""

# Verificar variables de proxy
$proxyUrl = docker exec ${containerName} printenv SIASCAFE_PROXY_URL 2>$null
$proxyHost = docker exec ${containerName} printenv SIASCAFE_PROXY_HOST 2>$null
$proxyPort = docker exec ${containerName} printenv SIASCAFE_PROXY_PORT 2>$null
$proxyUser = docker exec ${containerName} printenv SIASCAFE_PROXY_USER 2>$null

if ($proxyUrl) {
    # Ocultar contraseña
    $proxyDisplay = $proxyUrl -replace '://([^:]+):([^@]+)@', '://$1:****@'
    Write-Host "  [OK] SIASCAFE_PROXY_URL está configurado" -ForegroundColor Green
    Write-Host "       $proxyDisplay" -ForegroundColor White
} elseif ($proxyHost -and $proxyPort) {
    Write-Host "  [OK] Proxy configurado por componentes separados" -ForegroundColor Green
    Write-Host "       Host: $proxyHost" -ForegroundColor White
    Write-Host "       Port: $proxyPort" -ForegroundColor White
    if ($proxyUser) {
        Write-Host "       User: $proxyUser" -ForegroundColor White
    }
} else {
    Write-Host "  [ERROR] No se encontró configuración de proxy" -ForegroundColor Red
    Write-Host ""
    Write-Host "  Verifica que tu archivo .env tenga:" -ForegroundColor Yellow
    Write-Host "    SIASCAFE_PROXY_URL=http://usuario:password@brd.superproxy.io:33335" -ForegroundColor White
}

Write-Host ""
Write-Host "[2] Verificando logs del contenedor..." -ForegroundColor Yellow
Write-Host ""

# Buscar logs relacionados con proxy
$proxyLogs = docker logs ${containerName} 2>&1 | Select-String -Pattern "proxy" -CaseSensitive:$false | Select-Object -Last 5

if ($proxyLogs) {
    Write-Host "  Logs relacionados con proxy:" -ForegroundColor Green
    $proxyLogs | ForEach-Object { Write-Host "    $_" -ForegroundColor White }
} else {
    Write-Host "  [WARN] No se encontraron logs de proxy" -ForegroundColor Yellow
    Write-Host "  Esto puede indicar que el proxy no se está usando" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "[3] Verificando archivo .env en el contenedor..." -ForegroundColor Yellow
Write-Host ""

# Verificar si existe .env en el contenedor
$envExists = docker exec ${containerName} test -f /app/.env 2>$null
if ($LASTEXITCODE -eq 0) {
    Write-Host "  [OK] Archivo .env existe en el contenedor" -ForegroundColor Green
    $proxyInEnv = docker exec ${containerName} grep "SIASCAFE_PROXY" /app/.env 2>$null | Select-Object -First 1
    if ($proxyInEnv) {
        # Ocultar contraseña
        $proxyInEnvDisplay = $proxyInEnv -replace '://([^:]+):([^@]+)@', '://$1:****@'
        Write-Host "  Configuración encontrada:" -ForegroundColor Green
        Write-Host "    $proxyInEnvDisplay" -ForegroundColor White
    } else {
        Write-Host "  [ERROR] No se encontró SIASCAFE_PROXY en .env del contenedor" -ForegroundColor Red
    }
} else {
    Write-Host "  [WARN] Archivo .env no encontrado en el contenedor" -ForegroundColor Yellow
    Write-Host "  Verifica que el volumen esté montado correctamente" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Recomendaciones" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Si el proxy no está configurado:" -ForegroundColor Yellow
Write-Host "  1. Actualiza tu archivo .env local con:" -ForegroundColor White
Write-Host "     SIASCAFE_PROXY_URL=http://brd-customer-hl_6ad5dde5-zone-datacenter_proxy1:vekb114yzhdx@brd.superproxy.io:33335" -ForegroundColor Gray
Write-Host ""
Write-Host "  2. Copia el .env al contenedor:" -ForegroundColor White
Write-Host "     docker cp .env ${containerName}:/app/.env" -ForegroundColor Gray
Write-Host ""
Write-Host "  3. Reinicia el contenedor:" -ForegroundColor White
Write-Host "     docker restart ${containerName}" -ForegroundColor Gray
Write-Host ""
Write-Host "  4. Verifica nuevamente:" -ForegroundColor White
Write-Host "     .\verify-proxy-config.ps1" -ForegroundColor Gray
Write-Host ""

