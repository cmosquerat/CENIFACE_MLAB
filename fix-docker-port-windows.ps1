# Script para solucionar problemas de puertos en Docker Windows
# Uso: .\fix-docker-port-windows.ps1

$containerName = "multilab-agroanalitica"

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Solución de Problemas de Puerto Docker" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

# 1. Detener contenedor
Write-Host "[1] Deteniendo contenedor..." -ForegroundColor Yellow
docker stop $containerName 2>$null
docker rm $containerName 2>$null
Write-Host "  [OK] Contenedor detenido y eliminado" -ForegroundColor Green

# 2. Verificar que el puerto está libre
Write-Host ""
Write-Host "[2] Verificando que el puerto 5005 está libre..." -ForegroundColor Yellow
$portInUse = Get-NetTCPConnection -LocalPort 5005 -ErrorAction SilentlyContinue
if ($portInUse) {
    Write-Host "  [WARN] Puerto 5005 está en uso. Deteniendo procesos..." -ForegroundColor Yellow
    $portInUse | ForEach-Object {
        $pid = $_.OwningProcess
        Write-Host "    Deteniendo proceso PID: $pid" -ForegroundColor White
        Stop-Process -Id $pid -Force -ErrorAction SilentlyContinue
    }
    Start-Sleep -Seconds 2
}

# 3. Obtener directorio actual
$currentDir = Get-Location
Write-Host ""
Write-Host "[3] Reiniciando contenedor con mapeo de puertos explícito..." -ForegroundColor Yellow

# 4. Reiniciar contenedor
docker run -d `
  --name $containerName `
  --restart=unless-stopped `
  -p 127.0.0.1:5005:5000 `
  --env-file .env `
  -v "${currentDir}\multilab.db:/app/multilab.db:ro" `
  -v "${currentDir}\static\pdfs:/app/static/pdfs" `
  multilab-agroanalitica:latest

if ($LASTEXITCODE -eq 0) {
    Write-Host "  [OK] Contenedor reiniciado" -ForegroundColor Green
} else {
    Write-Host "  [ERROR] Error al reiniciar contenedor" -ForegroundColor Red
    exit 1
}

# 5. Esperar a que inicie
Write-Host ""
Write-Host "[4] Esperando a que el contenedor inicie..." -ForegroundColor Yellow
Start-Sleep -Seconds 5

# 6. Verificar conexión
Write-Host ""
Write-Host "[5] Verificando conexión..." -ForegroundColor Yellow
$maxAttempts = 10
$attempt = 0
$connected = $false

while ($attempt -lt $maxAttempts) {
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:5005/health" -UseBasicParsing -TimeoutSec 3 -ErrorAction Stop
        if ($response.StatusCode -eq 200) {
            Write-Host "  [OK] Conexión exitosa!" -ForegroundColor Green
            Write-Host "  La aplicación está disponible en: http://localhost:5005" -ForegroundColor Cyan
            $connected = $true
            break
        }
    } catch {
        # Continuar intentando
    }
    $attempt++
    if ($attempt -lt $maxAttempts) {
        Start-Sleep -Seconds 2
    }
}

if (-not $connected) {
    Write-Host "  [WARN] No se pudo verificar la conexión automáticamente" -ForegroundColor Yellow
    Write-Host "  Prueba manualmente: Invoke-WebRequest -Uri 'http://localhost:5005/health'" -ForegroundColor Cyan
    Write-Host "  O revisa los logs: docker logs $containerName" -ForegroundColor Cyan
}

Write-Host ""
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Proceso completado" -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

