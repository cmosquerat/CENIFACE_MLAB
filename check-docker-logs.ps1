# Script para ver logs del contenedor Docker
# Uso: .\check-docker-logs.ps1

$containerName = "multilab-agroanalitica"

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Logs del contenedor $containerName" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

# Verificar que el contenedor existe
$containerExists = docker ps -a --format "{{.Names}}" | Select-String -Pattern "^${containerName}$"

if (-not $containerExists) {
    Write-Host "[ERROR] Contenedor $containerName no encontrado" -ForegroundColor Red
    Write-Host "[INFO] Lista de contenedores:" -ForegroundColor Yellow
    docker ps -a
    exit 1
}

# Ver estado del contenedor
Write-Host "[INFO] Estado del contenedor:" -ForegroundColor Green
docker ps --filter "name=$containerName" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
Write-Host ""

# Mostrar últimas 50 líneas de logs
Write-Host "[INFO] Últimas 50 líneas de logs:" -ForegroundColor Green
Write-Host "----------------------------------------" -ForegroundColor Gray
docker logs --tail=50 $containerName
Write-Host "----------------------------------------" -ForegroundColor Gray
Write-Host ""

# Opciones
Write-Host "Comandos útiles:" -ForegroundColor Cyan
Write-Host "  Ver logs en tiempo real:  docker logs -f $containerName" -ForegroundColor White
Write-Host "  Ver últimas 100 líneas:  docker logs --tail=100 $containerName" -ForegroundColor White
Write-Host "  Ver desde inicio:        docker logs $containerName" -ForegroundColor White
Write-Host "  Reiniciar contenedor:    docker restart $containerName" -ForegroundColor White
Write-Host ""

