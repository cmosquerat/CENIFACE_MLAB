# Script para actualizar .env con configuración de Bright Data
# Uso: .\update-env-brightdata.ps1

$envFile = ".env"

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Actualizando .env con Bright Data Proxy" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

# Verificar si .env existe
if (-not (Test-Path $envFile)) {
    Write-Host "[INFO] Archivo .env no existe. Creando desde env.example..." -ForegroundColor Yellow
    if (Test-Path "env.example") {
        Copy-Item "env.example" ".env"
        Write-Host "[OK] Archivo .env creado" -ForegroundColor Green
    } else {
        Write-Host "[ERROR] No se encontró env.example" -ForegroundColor Red
        exit 1
    }
}

# Leer contenido actual
$content = Get-Content $envFile -Raw

# Configuración de Bright Data
$brightDataProxy = "SIASCAFE_PROXY_URL=http://brd-customer-hl_6ad5dde5-zone-datacenter_proxy1:vekb114yzhdx@brd.superproxy.io:33335"

# Verificar si ya existe configuración de proxy
if ($content -match "SIASCAFE_PROXY_URL") {
    Write-Host "[INFO] Reemplazando configuración de proxy existente..." -ForegroundColor Yellow
    # Reemplazar línea existente
    $content = $content -replace "SIASCAFE_PROXY_URL=.*", $brightDataProxy
    # También eliminar líneas comentadas relacionadas
    $content = $content -replace "#.*SIASCAFE_PROXY.*", ""
    $content = $content -replace "SIASCAFE_PROXY_HOST=.*", ""
    $content = $content -replace "SIASCAFE_PROXY_PORT=.*", ""
    $content = $content -replace "SIASCAFE_PROXY_USER=.*", ""
    $content = $content -replace "SIASCAFE_PROXY_PASS=.*", ""
} else {
    Write-Host "[INFO] Agregando configuración de proxy..." -ForegroundColor Yellow
    # Agregar después de SIASCAFE_URL
    if ($content -match "SIASCAFE_URL=") {
        $content = $content -replace "(SIASCAFE_URL=.*)", "`$1`n`n# Bright Data Proxy (para evitar bloqueos geográficos)`n$brightDataProxy"
    } else {
        # Agregar al final
        $content += "`n`n# Bright Data Proxy (para evitar bloqueos geográficos)`n$brightDataProxy`n"
    }
}

# Limpiar líneas vacías múltiples
$content = $content -replace "(`r?`n){3,}", "`n`n"

# Guardar archivo
Set-Content -Path $envFile -Value $content -NoNewline

Write-Host "[OK] Archivo .env actualizado con Bright Data Proxy" -ForegroundColor Green
Write-Host ""
Write-Host "Configuración agregada:" -ForegroundColor Cyan
Write-Host "  $brightDataProxy" -ForegroundColor White
Write-Host ""
Write-Host "Próximos pasos:" -ForegroundColor Yellow
Write-Host "  1. Reinicia el contenedor Docker:" -ForegroundColor White
Write-Host "     docker restart multilab-agroanalitica" -ForegroundColor Gray
Write-Host "  2. Verifica los logs:" -ForegroundColor White
Write-Host "     docker logs multilab-agroanalitica | grep PROXY" -ForegroundColor Gray
Write-Host ""

