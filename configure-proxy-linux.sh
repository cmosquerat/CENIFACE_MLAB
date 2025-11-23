#!/bin/bash

# Script rápido para configurar proxy en Docker daemon (Linux)
# Uso: sudo ./configure-proxy-linux.sh

set -e

# Leer configuración desde .env o usar valores por defecto
PROXY_HOST="brd.superproxy.io"
PROXY_PORT="33335"
PROXY_USER="brd-customer-hl_6ad5dde5-zone-datacenter_proxy1"
PROXY_PASS="vekb114yzhdx"
PROXY_COUNTRY="CO"

if [ -f ".env" ]; then
    while IFS='=' read -r key value; do
        [[ "$key" =~ ^#.*$ ]] && continue
        [[ -z "$key" ]] && continue
        key=$(echo "$key" | xargs)
        value=$(echo "$value" | xargs)
        case "$key" in
            SIASCAFE_PROXY_HOST) PROXY_HOST="$value" ;;
            SIASCAFE_PROXY_PORT) PROXY_PORT="$value" ;;
            SIASCAFE_PROXY_USER) PROXY_USER="$value" ;;
            SIASCAFE_PROXY_PASS) PROXY_PASS="$value" ;;
            SIASCAFE_PROXY_COUNTRY) PROXY_COUNTRY="$value" ;;
        esac
    done < .env
fi

# Construir username con país
if [ -n "$PROXY_COUNTRY" ] && [[ ! "$PROXY_USER" =~ -country-$PROXY_COUNTRY ]]; then
    PROXY_USER="${PROXY_USER}-country-${PROXY_COUNTRY}"
fi

# Construir URL del proxy
PROXY_URL="http://${PROXY_USER}:${PROXY_PASS}@${PROXY_HOST}:${PROXY_PORT}"

echo "Configurando proxy: ${PROXY_HOST}:${PROXY_PORT}"
echo "Usuario: ${PROXY_USER}"

# Crear directorio si no existe
DOCKER_SERVICE_DIR="/etc/systemd/system/docker.service.d"
mkdir -p "$DOCKER_SERVICE_DIR"

# Crear archivo de configuración
cat > "$DOCKER_SERVICE_DIR/http-proxy.conf" <<EOF
[Service]
Environment="HTTP_PROXY=${PROXY_URL}"
Environment="HTTPS_PROXY=${PROXY_URL}"
Environment="NO_PROXY=localhost,127.0.0.1,::1,*.local"
EOF

echo "Archivo creado: $DOCKER_SERVICE_DIR/http-proxy.conf"

# Recargar y reiniciar Docker
systemctl daemon-reload
systemctl restart docker

echo "Docker reiniciado. Verificando..."
sleep 2

# Verificar
if systemctl show docker --property=Environment | grep -q "HTTP_PROXY"; then
    echo "✓ Proxy configurado correctamente"
    systemctl show docker --property=Environment | grep -i proxy
else
    echo "✗ Error: Proxy no detectado"
    exit 1
fi

