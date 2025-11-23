# Script de diagnóstico para Docker en Windows
# Uso: .\diagnose-docker-windows.ps1

$containerName = "multilab-agroanalitica"

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Diagnóstico Docker - Windows" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

# 1. Verificar que Docker está corriendo
Write-Host "[1] Verificando Docker..." -ForegroundColor Yellow
try {
    $dockerVersion = docker --version
    Write-Host "  [OK] Docker está instalado: $dockerVersion" -ForegroundColor Green
} catch {
    Write-Host "  [ERROR] Docker no está instalado o no está en PATH" -ForegroundColor Red
    exit 1
}

# 2. Verificar que el contenedor existe y está corriendo
Write-Host ""
Write-Host "[2] Verificando contenedor..." -ForegroundColor Yellow
$containerStatus = docker ps --filter "name=$containerName" --format "{{.Names}}\t{{.Status}}\t{{.Ports}}"
if ($containerStatus) {
    Write-Host "  [OK] Contenedor está corriendo:" -ForegroundColor Green
    Write-Host "  $containerStatus" -ForegroundColor White
} else {
    Write-Host "  [ERROR] Contenedor no está corriendo" -ForegroundColor Red
    Write-Host "  Intentando iniciar..." -ForegroundColor Yellow
    docker start $containerName
    Start-Sleep -Seconds 3
    $containerStatus = docker ps --filter "name=$containerName" --format "{{.Names}}\t{{.Status}}\t{{.Ports}}"
    if ($containerStatus) {
        Write-Host "  [OK] Contenedor iniciado" -ForegroundColor Green
    } else {
        Write-Host "  [ERROR] No se pudo iniciar el contenedor" -ForegroundColor Red
        exit 1
    }
}

# 3. Verificar mapeo de puertos
Write-Host ""
Write-Host "[3] Verificando mapeo de puertos..." -ForegroundColor Yellow
$portMapping = docker port $containerName 2>$null
if ($portMapping) {
    Write-Host "  [OK] Puertos mapeados:" -ForegroundColor Green
    Write-Host "  $portMapping" -ForegroundColor White
} else {
    Write-Host "  [ERROR] No se encontró mapeo de puertos" -ForegroundColor Red
    Write-Host "  Verificando configuración del contenedor..." -ForegroundColor Yellow
    docker inspect $containerName --format='{{range $p, $conf := .NetworkSettings.Ports}}{{$p}} -> {{(index $conf 0).HostPort}}{{"\n"}}{{end}}'
}

# 4. Verificar que el puerto 5000 está escuchando en Windows
Write-Host ""
Write-Host "[4] Verificando puerto 5000 en Windows..." -ForegroundColor Yellow
$port5000 = Get-NetTCPConnection -LocalPort 5000 -ErrorAction SilentlyContinue
if ($port5000) {
    Write-Host "  [OK] Puerto 5000 está en uso:" -ForegroundColor Green
    $port5000 | ForEach-Object {
        Write-Host "    Estado: $($_.State) | PID: $($_.OwningProcess)" -ForegroundColor White
    }
} else {
    Write-Host "  [WARN] Puerto 5000 no está escuchando en Windows" -ForegroundColor Yellow
    Write-Host "  Esto puede indicar un problema con el mapeo de puertos de Docker" -ForegroundColor Yellow
}

# 5. Probar conexión desde dentro del contenedor
Write-Host ""
Write-Host "[5] Probando conexión desde dentro del contenedor..." -ForegroundColor Yellow
$healthCheck = docker exec $containerName curl -s http://localhost:5000/health 2>$null
if ($healthCheck) {
    Write-Host "  [OK] Servicio responde desde dentro del contenedor:" -ForegroundColor Green
    Write-Host "  $healthCheck" -ForegroundColor White
} else {
    Write-Host "  [ERROR] Servicio no responde desde dentro del contenedor" -ForegroundColor Red
    Write-Host "  Verificando logs..." -ForegroundColor Yellow
    docker logs --tail=20 $containerName
}

# 6. Probar conexión desde Windows
Write-Host ""
Write-Host "[6] Probando conexión desde Windows..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "http://localhost:5000/health" -UseBasicParsing -TimeoutSec 5 -ErrorAction Stop
    Write-Host "  [OK] Conexión exitosa desde Windows:" -ForegroundColor Green
    Write-Host "  Status: $($response.StatusCode)" -ForegroundColor White
    Write-Host "  Contenido: $($response.Content)" -ForegroundColor White
} catch {
    Write-Host "  [ERROR] No se puede conectar desde Windows:" -ForegroundColor Red
    Write-Host "  $($_.Exception.Message)" -ForegroundColor Red
    Write-Host ""
    Write-Host "  Posibles soluciones:" -ForegroundColor Yellow
    Write-Host "  1. Verificar que Docker Desktop está corriendo" -ForegroundColor White
    Write-Host "  2. Reiniciar Docker Desktop" -ForegroundColor White
    Write-Host "  3. Verificar firewall de Windows" -ForegroundColor White
    Write-Host "  4. Probar con: docker restart $containerName" -ForegroundColor White
}

# 7. Verificar firewall de Windows
Write-Host ""
Write-Host "[7] Verificando firewall de Windows..." -ForegroundColor Yellow
$firewallRules = Get-NetFirewallRule -DisplayName "*Docker*" -ErrorAction SilentlyContinue
if ($firewallRules) {
    Write-Host "  [INFO] Reglas de firewall relacionadas con Docker encontradas" -ForegroundColor Green
} else {
    Write-Host "  [WARN] No se encontraron reglas específicas de Docker en el firewall" -ForegroundColor Yellow
}

# 8. Verificar configuración de red de Docker
Write-Host ""
Write-Host "[8] Verificando configuración de red..." -ForegroundColor Yellow
$networkInfo = docker network inspect bridge --format='{{range .Containers}}{{.Name}}: {{.IPv4Address}}{{"\n"}}{{end}}' 2>$null
if ($networkInfo) {
    Write-Host "  [INFO] Contenedores en red bridge:" -ForegroundColor Green
    Write-Host "  $networkInfo" -ForegroundColor White
}

# Resumen
Write-Host ""
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Resumen" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Si la conexión falla, prueba:" -ForegroundColor Yellow
Write-Host "  1. docker restart $containerName" -ForegroundColor White
Write-Host "  2. Reiniciar Docker Desktop" -ForegroundColor White
Write-Host "  3. Verificar que el puerto 5000 no está bloqueado por otro programa" -ForegroundColor White
Write-Host "  4. Probar con: netstat -ano | findstr :5000" -ForegroundColor White
Write-Host ""

