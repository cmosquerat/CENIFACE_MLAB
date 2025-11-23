# Script de despliegue Docker con proxy bridge (PowerShell)
# Usa docker-compose con proxy-bridge para manejar autenticación
# Uso: .\docker-run-with-proxy.ps1

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Despliegue con Proxy Bridge (Windows)" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

# Verificar Docker y Docker Compose
if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    Write-Host "[ERROR] Docker no está instalado" -ForegroundColor Red
    exit 1
}

if (-not (Get-Command docker -ErrorAction SilentlyContinue).Source) {
    Write-Host "[ERROR] Docker Compose no está disponible" -ForegroundColor Red
    exit 1
}

Write-Host "[INFO] Docker encontrado" -ForegroundColor Green

# Verificar archivo .env
if (-not (Test-Path ".env")) {
    Write-Host "[WARN] Archivo .env no encontrado" -ForegroundColor Yellow
    if (Test-Path ".env.example") {
        Copy-Item ".env.example" ".env"
        Write-Host "[INFO] Archivo .env creado desde .env.example" -ForegroundColor Green
    }
}

# Crear directorios
Write-Host "[INFO] Creando directorios necesarios..." -ForegroundColor Green
New-Item -ItemType Directory -Force -Path "static\pdfs" | Out-Null
New-Item -ItemType Directory -Force -Path "static\images" | Out-Null

# Verificar docker-compose.yml
if (-not (Test-Path "docker-compose.yml")) {
    Write-Host "[ERROR] docker-compose.yml no encontrado" -ForegroundColor Red
    exit 1
}

# Detener contenedores existentes
Write-Host "[INFO] Deteniendo contenedores existentes..." -ForegroundColor Green
docker compose down 2>$null

# Construir e iniciar servicios
Write-Host "[INFO] Construyendo e iniciando servicios..." -ForegroundColor Green
Write-Host "[INFO] El proxy-bridge manejará la autenticación automáticamente" -ForegroundColor Green

docker compose up -d --build

if ($LASTEXITCODE -ne 0) {
    Write-Host "[ERROR] Error al iniciar servicios" -ForegroundColor Red
    exit 1
}

Write-Host "[INFO] Servicios iniciados" -ForegroundColor Green

# Esperar a que los servicios estén listos
Write-Host "[INFO] Esperando a que los servicios estén listos..." -ForegroundColor Green
Start-Sleep -Seconds 5

# Verificar estado
Write-Host "[INFO] Verificando estado de los servicios..." -ForegroundColor Green
docker compose ps

# Verificar proxy bridge
Write-Host "[INFO] Verificando proxy bridge..." -ForegroundColor Green
$proxyStatus = docker compose ps | Select-String "proxy-bridge"
if ($proxyStatus -match "Up") {
    Write-Host "  [OK] Proxy bridge está corriendo" -ForegroundColor Green
} else {
    Write-Host "  [WARN] Proxy bridge no está corriendo" -ForegroundColor Yellow
}

# Verificar aplicación
Write-Host "[INFO] Verificando aplicación..." -ForegroundColor Green
$maxAttempts = 15
$attempt = 0
$appReady = $false

while ($attempt -lt $maxAttempts) {
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:5005/health" -UseBasicParsing -TimeoutSec 3 -ErrorAction Stop
        if ($response.StatusCode -eq 200) {
            Write-Host "  [OK] Aplicación está funcionando" -ForegroundColor Green
            $appReady = $true
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

if (-not $appReady) {
    Write-Host "  [WARN] Aplicación no respondió después de $maxAttempts intentos" -ForegroundColor Yellow
    Write-Host "  Revisa logs: docker compose logs multilab-web" -ForegroundColor Cyan
}

Write-Host ""
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "[OK] Despliegue completado!" -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Servicios disponibles:" -ForegroundColor White
Write-Host "  - Aplicación: http://localhost:5005" -ForegroundColor Cyan
Write-Host "  - Proxy Bridge: http://localhost:8080 (interno)" -ForegroundColor Cyan
Write-Host ""
Write-Host "Comandos útiles:" -ForegroundColor White
Write-Host "  Ver logs:        docker compose logs -f" -ForegroundColor Gray
Write-Host "  Ver logs app:    docker compose logs -f multilab-web" -ForegroundColor Gray
Write-Host "  Ver logs proxy:  docker compose logs -f proxy-bridge" -ForegroundColor Gray
Write-Host "  Detener:         docker compose down" -ForegroundColor Gray
Write-Host "  Reiniciar:       docker compose restart" -ForegroundColor Gray
Write-Host "  Estado:          docker compose ps" -ForegroundColor Gray
Write-Host ""

