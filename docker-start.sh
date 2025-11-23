#!/bin/bash
# Script de inicio rápido para Docker

set -e

echo "=========================================="
echo "Multilab Agroanalítica - Docker Setup"
echo "=========================================="
echo ""

# Verificar que Docker está instalado
if ! command -v docker &> /dev/null; then
    echo "ERROR: Docker no está instalado"
    echo "Instala Docker desde: https://docs.docker.com/get-docker/"
    exit 1
fi

# Verificar que Docker Compose está instalado
if ! command -v docker-compose &> /dev/null; then
    echo "ADVERTENCIA: docker-compose no está instalado"
    echo "Se usará 'docker compose' (versión integrada)"
    DOCKER_COMPOSE_CMD="docker compose"
else
    DOCKER_COMPOSE_CMD="docker-compose"
fi

# Verificar que existe .env
if [ ! -f ".env" ]; then
    echo "Creando archivo .env desde env.example..."
    if [ -f "env.example" ]; then
        cp env.example .env
        echo "✓ Archivo .env creado. Edítalo si es necesario."
    else
        echo "ADVERTENCIA: env.example no encontrado"
        echo "Creando .env básico..."
        cat > .env << EOF
HOST=0.0.0.0
PORT=5005
DEBUG=False
DB_PATH=multilab.db
SIASCAFE_BASE_URL=https://agroclima.cenicafe.org
PDF_STORAGE_DIR=/tmp/siascafe_pdfs
EOF
    fi
fi

# Verificar que existe la base de datos
if [ ! -f "multilab.db" ]; then
    echo "ADVERTENCIA: multilab.db no encontrado"
    echo "Algunas funcionalidades pueden no estar disponibles"
fi

echo ""
echo "Construyendo imagen Docker..."
$DOCKER_COMPOSE_CMD build

echo ""
echo "Iniciando contenedor..."
$DOCKER_COMPOSE_CMD up -d

echo ""
echo "Esperando a que el servidor esté listo..."
sleep 5

# Verificar salud del servidor
if curl -f http://localhost:5005/health &> /dev/null; then
    echo ""
    echo "=========================================="
    echo "✓ Servidor iniciado correctamente!"
    echo "=========================================="
    echo ""
    echo "Aplicación disponible en: http://localhost:5005"
    echo ""
    echo "Para ver los logs:"
    echo "  $DOCKER_COMPOSE_CMD logs -f"
    echo ""
    echo "Para detener el servidor:"
    echo "  $DOCKER_COMPOSE_CMD down"
    echo ""
else
    echo ""
    echo "ADVERTENCIA: El servidor puede estar aún iniciando"
    echo "Verifica los logs con: $DOCKER_COMPOSE_CMD logs -f"
    echo ""
fi

