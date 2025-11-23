#!/bin/bash
# Script de debug rápido para contenedor Docker

CONTAINER_NAME="multilab-agroanalitica"

echo "=========================================="
echo "DEBUG - Multilab Agroanalítica Docker"
echo "=========================================="
echo ""

echo "=== 1. Estado del Contenedor ==="
docker ps -a | grep $CONTAINER_NAME || echo "Contenedor no encontrado"
echo ""

echo "=== 2. Últimos 50 líneas de Logs ==="
docker logs --tail 50 $CONTAINER_NAME 2>&1 || echo "No se pudieron obtener logs"
echo ""

echo "=== 3. Variables de Entorno Importantes ==="
docker exec $CONTAINER_NAME env 2>/dev/null | grep -E "PORT|HOST|DEBUG|DB_PATH|FLASK" || echo "Contenedor no está corriendo"
echo ""

echo "=== 4. Verificando Archivos Críticos ==="
docker exec $CONTAINER_NAME sh -c 'test -f /app/app.py && echo "✓ app.py existe" || echo "✗ app.py NO existe"' 2>/dev/null || echo "No se puede verificar"
docker exec $CONTAINER_NAME sh -c 'test -f /app/multilab.db && echo "✓ multilab.db existe" || echo "✗ multilab.db NO existe"' 2>/dev/null || echo "No se puede verificar"
docker exec $CONTAINER_NAME sh -c 'test -d /app/templates && echo "✓ templates existe" || echo "✗ templates NO existe"' 2>/dev/null || echo "No se puede verificar"
echo ""

echo "=== 5. Verificando Dependencias ==="
docker exec $CONTAINER_NAME python3 --version 2>/dev/null || echo "Python no encontrado"
docker exec $CONTAINER_NAME google-chrome --version 2>/dev/null || echo "Chrome no encontrado"
echo ""

echo "=== 6. Verificando Puerto ==="
docker exec $CONTAINER_NAME sh -c 'ss -tlnp 2>/dev/null | grep 5005 || netstat -tlnp 2>/dev/null | grep 5005 || echo "Puerto 5005 no está escuchando"' 2>/dev/null || echo "No se puede verificar puerto"
echo ""

echo "=========================================="
echo "Para ver logs en tiempo real:"
echo "  docker logs -f $CONTAINER_NAME"
echo ""
echo "Para entrar al contenedor:"
echo "  docker exec -it $CONTAINER_NAME /bin/bash"
echo ""
echo "Para ejecutar en modo interactivo:"
echo "  docker run -it --rm -p 5005:5005 --env-file .env multilab-agroanalitica /bin/bash"
echo "=========================================="

