# Script de despliegue Docker para PowerShell (versión rápida sin verificación de salud)
# Uso: .\docker-run-fast.ps1

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

# Detectar si se está usando MySQL con IP de red local
if (Test-Path ".env") {
    $envContent = Get-Content ".env" -Raw
    if ($envContent -match "DB_HOST\s*=\s*([^\r\n]+)") {
        $dbHost = $matches[1].Trim().Trim('"').Trim("'")
        if ($dbHost -match "^10\.|^192\.168\.|^172\.(1[6-9]|2[0-9]|3[0-1])\.") {
            Write-Host "[INFO] IP de red local detectada ($dbHost)" -ForegroundColor Yellow
        }
    }
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

# Esperar un momento
Start-Sleep -Seconds 2

# Verificar que el contenedor está corriendo (sin verificar salud HTTP)
$containerStatus = docker ps --format "{{.Names}}" | Select-String -Pattern "^${containerName}$"
if ($containerStatus) {
    Write-Host "[INFO] Contenedor está corriendo" -ForegroundColor Green
} else {
    Write-Host "[WARN] El contenedor no aparece en la lista de contenedores corriendo." -ForegroundColor Yellow
    Write-Host "[INFO] Revisa los logs con: docker logs $containerName" -ForegroundColor Cyan
}

# Mostrar información
Write-Host ""
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "[INFO] Despliegue completado!" -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "La aplicación debería estar disponible en:" -ForegroundColor White
Write-Host "  - http://localhost:5005" -ForegroundColor Cyan
Write-Host ""
Write-Host "El contenedor se reiniciará automáticamente:" -ForegroundColor White
Write-Host "  - Si se detiene inesperadamente" -ForegroundColor Gray
Write-Host "  - Si el servidor se reinicia" -ForegroundColor Gray
Write-Host "  - Si Docker se reinicia" -ForegroundColor Gray
Write-Host ""
Write-Host "Comandos útiles:" -ForegroundColor White
Write-Host "  Ver logs:        docker logs -f $containerName" -ForegroundColor Gray
Write-Host "  Verificar salud: curl http://localhost:5005/health" -ForegroundColor Gray
Write-Host "  Detener:         docker stop $containerName" -ForegroundColor Gray
Write-Host "  Iniciar:         docker start $containerName" -ForegroundColor Gray
Write-Host "  Reiniciar:       docker restart $containerName" -ForegroundColor Gray
Write-Host "  Estado:          docker ps | Select-String $containerName" -ForegroundColor Gray
Write-Host ""

