# Comando simple para detener servicios en puerto 5000
# Uso: .\stop-port-5000-simple.ps1

# Detener procesos que usan el puerto 5000
Get-NetTCPConnection -LocalPort 5000 -ErrorAction SilentlyContinue | 
    ForEach-Object { 
        $processId = $_.OwningProcess
        Write-Host "Deteniendo proceso PID: $processId"
        Stop-Process -Id $processId -Force -ErrorAction SilentlyContinue
    }

# Detener contenedores Docker en puerto 5000
docker ps --format "{{.ID}}" --filter "publish=5000" | ForEach-Object {
    Write-Host "Deteniendo contenedor Docker: $_"
    docker stop $_ 2>$null
}

Write-Host "Puerto 5000 liberado"

