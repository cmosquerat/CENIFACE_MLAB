#!/bin/bash

# Script para verificar configuración de proxy
# Uso: ./verify-proxy-config.sh

echo "=========================================="
echo "Verificación de Configuración de Proxy"
echo "=========================================="
echo ""

CONTAINER_NAME="multilab-agroanalitica"

# Verificar si el contenedor está corriendo
if ! docker ps --format "{{.Names}}" | grep -q "^${CONTAINER_NAME}$"; then
    echo "[ERROR] Contenedor ${CONTAINER_NAME} no está corriendo"
    exit 1
fi

echo "[1] Verificando variables de entorno en el contenedor..."
echo ""

# Verificar variables de proxy
PROXY_URL=$(docker exec ${CONTAINER_NAME} printenv SIASCAFE_PROXY_URL 2>/dev/null || echo "")
PROXY_HOST=$(docker exec ${CONTAINER_NAME} printenv SIASCAFE_PROXY_HOST 2>/dev/null || echo "")
PROXY_PORT=$(docker exec ${CONTAINER_NAME} printenv SIASCAFE_PROXY_PORT 2>/dev/null || echo "")
PROXY_USER=$(docker exec ${CONTAINER_NAME} printenv SIASCAFE_PROXY_USER 2>/dev/null || echo "")

if [ -n "$PROXY_URL" ]; then
    # Ocultar contraseña
    PROXY_DISPLAY=$(echo "$PROXY_URL" | sed 's|://\([^:]*\):\([^@]*\)@|://\1:****@|')
    echo "  [OK] SIASCAFE_PROXY_URL está configurado"
    echo "       $PROXY_DISPLAY"
elif [ -n "$PROXY_HOST" ] && [ -n "$PROXY_PORT" ]; then
    echo "  [OK] Proxy configurado por componentes separados"
    echo "       Host: $PROXY_HOST"
    echo "       Port: $PROXY_PORT"
    if [ -n "$PROXY_USER" ]; then
        echo "       User: $PROXY_USER"
    fi
else
    echo "  [ERROR] No se encontró configuración de proxy"
    echo ""
    echo "  Verifica que tu archivo .env tenga:"
    echo "    SIASCAFE_PROXY_URL=http://usuario:password@brd.superproxy.io:33335"
fi

echo ""
echo "[2] Verificando logs del contenedor..."
echo ""

# Buscar logs relacionados con proxy
PROXY_LOGS=$(docker logs ${CONTAINER_NAME} 2>&1 | grep -i "proxy" | tail -5)

if [ -n "$PROXY_LOGS" ]; then
    echo "  Logs relacionados con proxy:"
    echo "$PROXY_LOGS" | sed 's/^/    /'
else
    echo "  [WARN] No se encontraron logs de proxy"
    echo "  Esto puede indicar que el proxy no se está usando"
fi

echo ""
echo "[3] Verificando archivo .env en el contenedor..."
echo ""

# Verificar si existe .env en el contenedor
if docker exec ${CONTAINER_NAME} test -f /app/.env 2>/dev/null; then
    echo "  [OK] Archivo .env existe en el contenedor"
    PROXY_IN_ENV=$(docker exec ${CONTAINER_NAME} grep "SIASCAFE_PROXY" /app/.env 2>/dev/null | head -1 || echo "")
    if [ -n "$PROXY_IN_ENV" ]; then
        # Ocultar contraseña
        PROXY_IN_ENV_DISPLAY=$(echo "$PROXY_IN_ENV" | sed 's|://\([^:]*\):\([^@]*\)@|://\1:****@|')
        echo "  Configuración encontrada:"
        echo "    $PROXY_IN_ENV_DISPLAY"
    else
        echo "  [ERROR] No se encontró SIASCAFE_PROXY en .env del contenedor"
    fi
else
    echo "  [WARN] Archivo .env no encontrado en el contenedor"
    echo "  Verifica que el volumen esté montado correctamente"
fi

echo ""
echo "=========================================="
echo "Recomendaciones"
echo "=========================================="
echo ""
echo "Si el proxy no está configurado:"
echo "  1. Actualiza tu archivo .env local con:"
echo "     SIASCAFE_PROXY_URL=http://brd-customer-hl_6ad5dde5-zone-datacenter_proxy1:vekb114yzhdx@brd.superproxy.io:33335"
echo ""
echo "  2. Copia el .env al contenedor:"
echo "     docker cp .env ${CONTAINER_NAME}:/app/.env"
echo ""
echo "  3. Reinicia el contenedor:"
echo "     docker restart ${CONTAINER_NAME}"
echo ""
echo "  4. Verifica nuevamente:"
echo "     ./verify-proxy-config.sh"
echo ""

