#!/bin/bash

# Script de despliegue Docker con proxy bridge (Linux)
# Usa docker-compose con proxy-bridge para manejar autenticación
# Uso: ./docker-run-with-proxy-linux.sh

set -e

echo "=========================================="
echo "Despliegue con Proxy Bridge (Linux)"
echo "=========================================="
echo ""

# Colores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

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

# Verificar Docker y Docker Compose
if ! command -v docker &> /dev/null; then
    error "Docker no está instalado"
fi

if ! command -v docker compose &> /dev/null && ! command -v docker-compose &> /dev/null; then
    error "Docker Compose no está instalado"
fi

info "Docker y Docker Compose encontrados"

# Verificar archivo .env
if [ ! -f ".env" ]; then
    warn "Archivo .env no encontrado"
    if [ -f ".env.example" ]; then
        cp .env.example .env
        info "Archivo .env creado desde .env.example"
    fi
fi

# Crear directorios
info "Creando directorios necesarios..."
mkdir -p static/pdfs static/images
chmod 755 static/pdfs 2>/dev/null || true

# Verificar docker-compose.yml
if [ ! -f "docker-compose.yml" ]; then
    error "docker-compose.yml no encontrado"
fi

# Detener contenedores existentes
info "Deteniendo contenedores existentes..."
docker compose down 2>/dev/null || true

# Construir e iniciar servicios
info "Construyendo e iniciando servicios..."
info "El proxy-bridge manejará la autenticación automáticamente"

docker compose up -d --build

if [ $? -ne 0 ]; then
    error "Error al iniciar servicios"
fi

info "Servicios iniciados"

# Esperar a que los servicios estén listos
info "Esperando a que los servicios estén listos..."
sleep 5

# Verificar estado
info "Verificando estado de los servicios..."
docker compose ps

# Verificar proxy bridge
info "Verificando proxy bridge..."
if docker compose ps | grep -q "proxy-bridge.*Up"; then
    info "✓ Proxy bridge está corriendo"
else
    warn "✗ Proxy bridge no está corriendo"
fi

# Verificar aplicación
info "Verificando aplicación..."
for i in {1..15}; do
    if curl -f http://localhost:5005/health &> /dev/null; then
        info "✓ Aplicación está funcionando"
        break
    fi
    if [ $i -eq 15 ]; then
        warn "Aplicación no respondió después de 15 intentos"
        warn "Revisa logs: docker compose logs multilab-web"
    else
        sleep 2
    fi
done

# Verificar que el proxy funciona
info "Verificando que el proxy funciona..."
PROXY_IP=$(docker compose exec -T multilab-web curl -s https://api.ipify.org 2>/dev/null || echo "")
if [ -n "$PROXY_IP" ]; then
    info "✓ Proxy funcionando. IP detectada: $PROXY_IP"
else
    warn "No se pudo verificar el proxy automáticamente"
fi

echo ""
echo "=========================================="
info "Despliegue completado!"
echo "=========================================="
echo ""
echo "Servicios disponibles:"
echo "  - Aplicación: http://localhost:5005"
echo "  - Proxy Bridge: http://localhost:8080 (interno)"
echo ""
echo "Comandos útiles:"
echo "  Ver logs:        docker compose logs -f"
echo "  Ver logs app:    docker compose logs -f multilab-web"
echo "  Ver logs proxy:  docker compose logs -f proxy-bridge"
echo "  Detener:         docker compose down"
echo "  Reiniciar:       docker compose restart"
echo "  Estado:          docker compose ps"
echo ""

