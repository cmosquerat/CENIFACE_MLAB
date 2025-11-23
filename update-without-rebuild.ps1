# Script para actualizar aplicación sin rebuild completo (PowerShell)
# Solo copia archivos nuevos y reinicia el contenedor
# Uso: .\update-without-rebuild.ps1

$containerName = "multilab-agroanalitica"

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Actualización sin Rebuild" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

# Verificar que el contenedor existe y está corriendo
$containerStatus = docker ps --format "{{.Names}}" | Select-String -Pattern "^${containerName}$"
if (-not $containerStatus) {
    Write-Host "[ERROR] Contenedor ${containerName} no está corriendo" -ForegroundColor Red
    Write-Host "Ejecuta primero: .\docker-run-fast.ps1" -ForegroundColor Yellow
    exit 1
}

Write-Host "[INFO] Contenedor encontrado: ${containerName}" -ForegroundColor Green
Write-Host ""

# Lista de archivos a copiar
$filesToCopy = @(
    "app.py",
    "config.py",
    "database.py",
    "data_mapper.py",
    "siascafe_client.py",
    "templates",
    "static",
    ".env"
)

Write-Host "[INFO] Copiando archivos actualizados al contenedor..." -ForegroundColor Yellow
foreach ($file in $filesToCopy) {
    if (Test-Path $file) {
        Write-Host "  Copiando: $file" -ForegroundColor White
        # Si es un directorio, copiar recursivamente
        if ((Get-Item $file) -is [System.IO.DirectoryInfo]) {
            docker cp "${file}/." "${containerName}:/app/$file/"
        } else {
            docker cp "$file" "${containerName}:/app/"
        }
    } else {
        Write-Host "  [WARN] Archivo no encontrado: $file" -ForegroundColor Yellow
    }
}

# Forzar recarga de variables de entorno copiando .env
if (Test-Path ".env") {
    Write-Host "  [INFO] Forzando recarga de .env..." -ForegroundColor Cyan
    docker cp ".env" "${containerName}:/app/.env"
}

Write-Host ""
Write-Host "[INFO] Reiniciando contenedor para aplicar cambios..." -ForegroundColor Yellow
docker restart $containerName

Write-Host ""
Write-Host "[INFO] Esperando a que el contenedor inicie..." -ForegroundColor Yellow
Start-Sleep -Seconds 5

# Verificar salud
Write-Host "[INFO] Verificando salud del servicio..." -ForegroundColor Yellow
$maxAttempts = 10
$attempt = 0
$connected = $false

while ($attempt -lt $maxAttempts) {
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:5005/health" -UseBasicParsing -TimeoutSec 3 -ErrorAction Stop
        if ($response.StatusCode -eq 200) {
            Write-Host "[OK] Servicio está funcionando correctamente" -ForegroundColor Green
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
    Write-Host "[WARN] El servicio no respondió. Revisa los logs:" -ForegroundColor Yellow
    Write-Host "  docker logs ${containerName}" -ForegroundColor Cyan
}

Write-Host ""
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "[OK] Actualización completada" -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Ver logs: docker logs -f ${containerName}" -ForegroundColor Cyan
Write-Host ""

