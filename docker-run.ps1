# Script de despliegue Docker para PowerShell
# Uso: .\docker-run.ps1

# Obtener directorio actual
$currentDir = Get-Location

# Nombre del contenedor e imagen
$containerName = "multilab-agroanalitica"
$imageName = "multilab-agroanalitica:latest"

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Despliegue de Multilab Agroanalítica" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan

# Verificar que existe el archivo .env
if (-not (Test-Path ".env")) {
    Write-Host "[WARN] Archivo .env no encontrado." -ForegroundColor Yellow
    if (Test-Path "env.example") {
        Copy-Item "env.example" ".env"
        Write-Host "[INFO] Archivo .env creado desde env.example" -ForegroundColor Green
    } else {
        Write-Host "[ERROR] No se encontró env.example. Crea un archivo .env manualmente." -ForegroundColor Red
        exit 1
    }
}

# Verificar que existe la base de datos
if (-not (Test-Path "multilab.db")) {
    Write-Host "[WARN] Base de datos multilab.db no encontrada." -ForegroundColor Yellow
    $continue = Read-Host "¿Deseas continuar de todas formas? (s/N)"
    if ($continue -ne "s" -and $continue -ne "S") {
        Write-Host "[INFO] Despliegue cancelado." -ForegroundColor Yellow
        exit 0
    }
}

# Crear directorios necesarios
Write-Host "[INFO] Creando directorios necesarios..." -ForegroundColor Green
New-Item -ItemType Directory -Force -Path "static\pdfs" | Out-Null
New-Item -ItemType Directory -Force -Path "static\images" | Out-Null

# Detener y eliminar contenedor existente si existe
if (docker ps -a --format '{{.Names}}' | Select-String -Pattern "^${containerName}$") {
    Write-Host "[INFO] Deteniendo contenedor existente..." -ForegroundColor Green
    docker stop $containerName 2>$null
    docker rm $containerName 2>$null
}

# Construir imagen si no existe
Write-Host "[INFO] Verificando imagen Docker..." -ForegroundColor Green
if (-not (docker images --format '{{.Repository}}:{{.Tag}}' | Select-String -Pattern "^${imageName}$")) {
    Write-Host "[INFO] Construyendo imagen Docker (esto puede tardar varios minutos)..." -ForegroundColor Green
    docker build -t $imageName .
    if ($LASTEXITCODE -ne 0) {
        Write-Host "[ERROR] Error al construir la imagen Docker." -ForegroundColor Red
        exit 1
    }
    Write-Host "[INFO] Imagen construida exitosamente" -ForegroundColor Green
} else {
    Write-Host "[INFO] Imagen ya existe, omitiendo construcción" -ForegroundColor Green
}

# Ejecutar contenedor
Write-Host "[INFO] Iniciando contenedor con reinicio automático..." -ForegroundColor Green

docker run -d `
  --name $containerName `
  --restart=unless-stopped `
  -p 127.0.0.1:5005:5000 `
  --env-file .env `
  -v "${currentDir}\multilab.db:/app/multilab.db:ro" `
  -v "${currentDir}\static\pdfs:/app/static/pdfs" `
  $imageName

if ($LASTEXITCODE -ne 0) {
    Write-Host "[ERROR] Error al iniciar el contenedor." -ForegroundColor Red
    exit 1
}

Write-Host "[INFO] Contenedor iniciado exitosamente" -ForegroundColor Green

# Esperar a que el contenedor inicie
Write-Host "[INFO] Esperando a que el contenedor inicie..." -ForegroundColor Green
Start-Sleep -Seconds 3

# Verificar que el contenedor está corriendo
$containerStatus = docker ps --format "{{.Names}}" | Select-String -Pattern "^${containerName}$"
if (-not $containerStatus) {
    Write-Host "[ERROR] El contenedor no está corriendo. Revisa los logs:" -ForegroundColor Red
    Write-Host "  docker logs $containerName" -ForegroundColor Cyan
    exit 1
}
Write-Host "[INFO] Contenedor está corriendo" -ForegroundColor Green

# Verificar salud del servicio
Write-Host "[INFO] Verificando salud del servicio..." -ForegroundColor Green
$maxAttempts = 15
$attempt = 0
$serviceReady = $false

while ($attempt -lt $maxAttempts) {
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:5005/health" -UseBasicParsing -TimeoutSec 3 -ErrorAction Stop
        if ($response.StatusCode -eq 200) {
            Write-Host "[INFO] Servicio está funcionando correctamente!" -ForegroundColor Green
            $serviceReady = $true
            break
        }
    } catch {
        # Mostrar progreso cada 3 intentos
        if (($attempt + 1) % 3 -eq 0) {
            Write-Host "  Intentando... ($($attempt + 1)/$maxAttempts)" -ForegroundColor Gray
        }
    }
    $attempt++
    if ($attempt -lt $maxAttempts) {
        Start-Sleep -Seconds 2
    }
}

if (-not $serviceReady) {
    Write-Host "[WARN] El servicio no respondió después de $maxAttempts intentos." -ForegroundColor Yellow
    Write-Host "[INFO] Esto puede ser normal si el contenedor aún está iniciando." -ForegroundColor Yellow
    Write-Host "[INFO] Revisa los logs con: docker logs -f $containerName" -ForegroundColor Cyan
    Write-Host "[INFO] O verifica el estado con: docker ps | Select-String $containerName" -ForegroundColor Cyan
} else {
    Write-Host "[INFO] Verificación completada exitosamente" -ForegroundColor Green
}

# Mostrar información
Write-Host ""
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "[INFO] Despliegue completado!" -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "La aplicación está disponible en:" -ForegroundColor White
Write-Host "  - http://localhost:5005" -ForegroundColor Cyan
Write-Host ""
Write-Host "El contenedor se reiniciará automáticamente:" -ForegroundColor White
Write-Host "  - Si se detiene inesperadamente" -ForegroundColor Gray
Write-Host "  - Si el servidor se reinicia" -ForegroundColor Gray
Write-Host "  - Si Docker se reinicia" -ForegroundColor Gray
Write-Host ""
Write-Host "Comandos útiles:" -ForegroundColor White
Write-Host "  Ver logs:        docker logs -f $containerName" -ForegroundColor Gray
Write-Host "  Detener:         docker stop $containerName" -ForegroundColor Gray
Write-Host "  Iniciar:         docker start $containerName" -ForegroundColor Gray
Write-Host "  Reiniciar:       docker restart $containerName" -ForegroundColor Gray
Write-Host "  Estado:          docker ps | Select-String $containerName" -ForegroundColor Gray
Write-Host "  Stats:           docker stats $containerName" -ForegroundColor Gray
Write-Host ""

