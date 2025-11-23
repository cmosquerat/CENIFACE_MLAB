# Script para detener servicios que usan el puerto 5000
# Uso: .\stop-port-5000.ps1

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Deteniendo servicios en puerto 5000" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan

# Obtener procesos que usan el puerto 5000
$connections = Get-NetTCPConnection -LocalPort 5000 -ErrorAction SilentlyContinue

if ($connections) {
    Write-Host "[INFO] Encontrados procesos usando el puerto 5000:" -ForegroundColor Yellow
    
    foreach ($conn in $connections) {
        $processId = $conn.OwningProcess
        $process = Get-Process -Id $processId -ErrorAction SilentlyContinue
        
        if ($process) {
            Write-Host "  - PID: $processId | Nombre: $($process.ProcessName) | Ruta: $($process.Path)" -ForegroundColor White
            
            # Detener el proceso
            try {
                Stop-Process -Id $processId -Force
                Write-Host "    [OK] Proceso $processId ($($process.ProcessName)) detenido" -ForegroundColor Green
            } catch {
                Write-Host "    [ERROR] No se pudo detener el proceso $processId : $_" -ForegroundColor Red
            }
        }
    }
    
    # Esperar un momento para que los procesos se detengan
    Start-Sleep -Seconds 2
    
    # Verificar si aún hay procesos usando el puerto
    $remaining = Get-NetTCPConnection -LocalPort 5000 -ErrorAction SilentlyContinue
    if ($remaining) {
        Write-Host "[WARN] Aún hay procesos usando el puerto 5000" -ForegroundColor Yellow
        Write-Host "[INFO] Intenta ejecutar como administrador o detén los procesos manualmente" -ForegroundColor Yellow
    } else {
        Write-Host "[INFO] Puerto 5000 liberado exitosamente" -ForegroundColor Green
    }
} else {
    Write-Host "[INFO] No se encontraron procesos usando el puerto 5000" -ForegroundColor Green
}

# También verificar contenedores Docker en el puerto 5000
Write-Host ""
Write-Host "[INFO] Verificando contenedores Docker..." -ForegroundColor Cyan

$dockerContainers = docker ps --format "{{.ID}} {{.Names}} {{.Ports}}" | Select-String "5000"

if ($dockerContainers) {
    Write-Host "[INFO] Contenedores Docker usando el puerto 5000:" -ForegroundColor Yellow
    
    foreach ($container in $dockerContainers) {
        $containerInfo = $container.ToString().Split(" ")
        $containerId = $containerInfo[0]
        $containerName = $containerInfo[1]
        
        Write-Host "  - ID: $containerId | Nombre: $containerName" -ForegroundColor White
        
        # Detener el contenedor
        try {
            docker stop $containerId
            Write-Host "    [OK] Contenedor $containerName detenido" -ForegroundColor Green
        } catch {
            Write-Host "    [ERROR] No se pudo detener el contenedor $containerName : $_" -ForegroundColor Red
        }
    }
} else {
    Write-Host "[INFO] No se encontraron contenedores Docker usando el puerto 5000" -ForegroundColor Green
}

Write-Host ""
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "[INFO] Proceso completado" -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Cyan

