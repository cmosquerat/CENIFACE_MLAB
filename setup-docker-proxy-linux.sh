#!/bin/bash

# Script para configurar proxy de Bright Data a nivel de Docker (Linux)
# Uso: ./setup-docker-proxy-linux.sh

set -e  # Salir si hay algún error

echo "=========================================="
echo "Configuración de Proxy para Docker (Linux)"
echo "=========================================="
echo ""

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
    exit 1
}

# Leer configuración desde .env
PROXY_HOST="brd.superproxy.io"
PROXY_PORT="33335"
PROXY_USER="brd-customer-hl_6ad5dde5-zone-datacenter_proxy1"
PROXY_PASS="vekb114yzhdx"
PROXY_COUNTRY="CO"

if [ -f ".env" ]; then
    while IFS='=' read -r key value; do
        # Ignorar comentarios y líneas vacías
        [[ "$key" =~ ^#.*$ ]] && continue
        [[ -z "$key" ]] && continue
        
        key=$(echo "$key" | xargs)
        value=$(echo "$value" | xargs)
        
        case "$key" in
            SIASCAFE_PROXY_HOST)
                PROXY_HOST="$value"
                ;;
            SIASCAFE_PROXY_PORT)
                PROXY_PORT="$value"
                ;;
            SIASCAFE_PROXY_USER)
                PROXY_USER="$value"
                ;;
            SIASCAFE_PROXY_PASS)
                PROXY_PASS="$value"
                ;;
            SIASCAFE_PROXY_COUNTRY)
                PROXY_COUNTRY="$value"
                ;;
        esac
    done < .env
fi

# Construir username con país
if [ -n "$PROXY_COUNTRY" ] && [[ ! "$PROXY_USER" =~ -country-$PROXY_COUNTRY ]]; then
    PROXY_USER="${PROXY_USER}-country-${PROXY_COUNTRY}"
fi

# Construir URL del proxy
PROXY_URL="http://${PROXY_USER}:${PROXY_PASS}@${PROXY_HOST}:${PROXY_PORT}"

info "Configuración del proxy:"
echo "  Host: $PROXY_HOST"
echo "  Port: $PROXY_PORT"
echo "  User: $PROXY_USER"
echo "  Country: $PROXY_COUNTRY"
echo ""

# Configurar proxy para Docker daemon (systemd) - Proxy transparente
info "[1] Configurando proxy para Docker daemon (transparente para contenedores)..."

DOCKER_SERVICE_DIR="/etc/systemd/system/docker.service.d"
DOCKER_PROXY_FILE="${DOCKER_SERVICE_DIR}/http-proxy.conf"

if [ ! -d "$DOCKER_SERVICE_DIR" ]; then
    sudo mkdir -p "$DOCKER_SERVICE_DIR"
    info "  Directorio creado: $DOCKER_SERVICE_DIR"
fi

# Crear archivo de configuración de proxy para Docker daemon
# Esto hace que TODOS los contenedores usen el proxy automáticamente
sudo tee "$DOCKER_PROXY_FILE" > /dev/null <<EOF
[Service]
Environment="HTTP_PROXY=${PROXY_URL}"
Environment="HTTPS_PROXY=${PROXY_URL}"
Environment="NO_PROXY=localhost,127.0.0.1,::1,*.local"
EOF

info "  [OK] Archivo de proxy creado: $DOCKER_PROXY_FILE"
info "  NOTA: El proxy será transparente para todos los contenedores"

# Recargar configuración de systemd y reiniciar Docker
info "[2] Recargando configuración de Docker..."
sudo systemctl daemon-reload
sudo systemctl restart docker

if [ $? -eq 0 ]; then
    info "  [OK] Docker reiniciado con configuración de proxy"
    info "  Todos los contenedores ahora usarán el proxy automáticamente"
else
    warn "  [WARN] No se pudo reiniciar Docker automáticamente"
    warn "  Ejecuta manualmente: sudo systemctl restart docker"
fi

# El proxy está configurado a nivel de Docker daemon
# No es necesario configurar nada dentro de los contenedores
info "[3] Proxy configurado a nivel de Docker daemon"
info "  Los contenedores usarán el proxy automáticamente sin configuración adicional"
echo ""

# Verificar configuración
info "[4] Verificando configuración..."
echo "  Verificando Docker daemon..."
if sudo systemctl show docker --property=Environment | grep -q "HTTP_PROXY"; then
    info "  [OK] Proxy configurado en Docker daemon"
    echo "  Configuración:"
    sudo systemctl show docker --property=Environment | grep -E "HTTP_PROXY|HTTPS_PROXY" | sed 's/^/    /'
else
    warn "  [WARN] Proxy no detectado en Docker daemon"
fi

echo ""
echo "=========================================="
info "[OK] Configuración completada"
echo "=========================================="
echo ""
echo "El proxy está configurado a nivel de Docker daemon."
echo "Todos los contenedores usarán el proxy automáticamente."
echo ""
echo "Ventajas de esta configuración:"
echo "  - Proxy transparente (no requiere configuración en contenedores)"
echo "  - Evita problemas de autenticación"
echo "  - Funciona para todo el tráfico de red"
echo ""
echo "Para verificar:"
echo "  docker run --rm alpine/curl curl -s https://api.ipify.org"
echo ""
echo "NOTA: Si cambias la configuración, ejecuta:"
echo "  sudo systemctl daemon-reload"
echo "  sudo systemctl restart docker"
echo ""

