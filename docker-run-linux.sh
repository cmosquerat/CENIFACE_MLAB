#!/bin/bash

# Script de despliegue Docker para Linux
# Uso: ./docker-run-linux.sh

set -e  # Salir si hay algún error

echo "=========================================="
echo "Despliegue de Multilab Agroanalítica (Linux)"
echo "=========================================="

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Función para imprimir mensajes
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

# Verificar que estamos en el directorio correcto
if [ ! -f "Dockerfile" ]; then
    error "No se encontró Dockerfile. Ejecuta este script desde el directorio raíz del proyecto."
fi

# Verificar Docker
if ! command -v docker &> /dev/null; then
    error "Docker no está instalado. Por favor instálalo primero."
fi

info "Docker encontrado: $(docker --version)"

# Verificar archivo .env
if [ ! -f ".env" ]; then
    warn "Archivo .env no encontrado. Creando desde .env.example..."
    if [ -f ".env.example" ]; then
        cp .env.example .env
        info "Archivo .env creado. Por favor edítalo con tus configuraciones."
    else
        error "No se encontró .env.example. Por favor crea un archivo .env manualmente."
    fi
fi

# Crear directorios necesarios
info "Creando directorios necesarios..."
mkdir -p static/pdfs
mkdir -p static/images
chmod 755 static/pdfs 2>/dev/null || true

# Verificar base de datos
if [ ! -f "multilab.db" ]; then
    warn "Base de datos multilab.db no encontrada en el directorio actual."
    warn "Asegúrate de tener la base de datos antes de continuar."
    read -p "¿Deseas continuar de todas formas? (s/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Ss]$ ]]; then
        error "Despliegue cancelado."
    fi
fi

# Nombre del contenedor e imagen
CONTAINER_NAME="multilab-agroanalitica"
IMAGE_NAME="multilab-agroanalitica:latest"

# Detener y eliminar contenedor existente si existe
if docker ps -a --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
    info "Deteniendo contenedor existente..."
    docker stop ${CONTAINER_NAME} 2>/dev/null || true
    docker rm ${CONTAINER_NAME} 2>/dev/null || true
fi

# Construir imagen si no existe
info "Verificando imagen Docker..."
if ! docker images --format '{{.Repository}}:{{.Tag}}' | grep -q "^${IMAGE_NAME}$"; then
    info "Construyendo imagen Docker (esto puede tardar varios minutos)..."
    docker build -t ${IMAGE_NAME} .
    if [ $? -ne 0 ]; then
        error "Error al construir la imagen Docker."
    fi
    info "Imagen construida exitosamente"
else
    info "Imagen ya existe, omitiendo construcción"
fi

# Obtener ruta absoluta del directorio actual
CURRENT_DIR=$(pwd)

# Detectar si se está usando MySQL con IP de red local
# Si DB_HOST está configurado y es una IP privada (10.x.x.x, 192.168.x.x, 172.16-31.x.x),
# usar --network host para acceso directo a la red local
USE_HOST_NETWORK=false
if [ -f ".env" ]; then
    DB_HOST=$(grep "^DB_HOST=" .env | cut -d'=' -f2 | tr -d '"' | tr -d "'" | xargs)
    if [ -n "$DB_HOST" ]; then
        # Verificar si es una IP privada (red local)
        if [[ $DB_HOST =~ ^10\. ]] || [[ $DB_HOST =~ ^192\.168\. ]] || [[ $DB_HOST =~ ^172\.(1[6-9]|2[0-9]|3[0-1])\. ]]; then
            USE_HOST_NETWORK=true
            info "IP de red local detectada ($DB_HOST), usando --network host para acceso directo"
        fi
    fi
fi

# Ejecutar contenedor con reinicio automático
info "Iniciando contenedor con reinicio automático..."
if [ "$USE_HOST_NETWORK" = true ]; then
    info "Modo: --network host (acceso directo a red local)"
    info "Puerto: 5000 (directo en el host)"
    docker run -d \
      --name ${CONTAINER_NAME} \
      --restart=unless-stopped \
      --network host \
      --env-file .env \
      -v ${CURRENT_DIR}/multilab.db:/app/multilab.db:ro \
      -v ${CURRENT_DIR}/static/pdfs:/app/static/pdfs \
      --memory=2g \
      --memory-swap=2g \
      ${IMAGE_NAME}
else
    info "Modo: red bridge (puerto mapeado)"
    info "Puerto externo: 5005 -> Puerto interno: 5000"
    docker run -d \
      --name ${CONTAINER_NAME} \
      --restart=unless-stopped \
      -p 5005:5000 \
      --env-file .env \
      -v ${CURRENT_DIR}/multilab.db:/app/multilab.db:ro \
      -v ${CURRENT_DIR}/static/pdfs:/app/static/pdfs \
      --memory=2g \
      --memory-swap=2g \
      ${IMAGE_NAME}
fi

if [ $? -ne 0 ]; then
    error "Error al iniciar el contenedor."
fi

info "Contenedor iniciado exitosamente"

# Esperar a que el contenedor esté listo
info "Esperando a que el contenedor inicie..."
sleep 3

# Verificar que el contenedor está corriendo
CONTAINER_STATUS=$(docker ps --format "{{.Names}}" | grep "^${CONTAINER_NAME}$")
if [ -n "$CONTAINER_STATUS" ]; then
    info "Contenedor está corriendo"
else
    warn "El contenedor no aparece en la lista de contenedores corriendo."
    info "Revisa los logs con: docker logs ${CONTAINER_NAME}"
fi

# Verificar política de reinicio
RESTART_POLICY=$(docker inspect ${CONTAINER_NAME} --format='{{.HostConfig.RestartPolicy.Name}}')
info "Política de reinicio configurada: ${RESTART_POLICY}"

# Verificar salud del servicio (opcional, no bloquea)
info "Verificando salud del servicio..."
for i in {1..10}; do
    if curl -f http://localhost:5005/health &> /dev/null; then
        info "Servicio está funcionando correctamente!"
        break
    fi
    if [ $i -eq 10 ]; then
        warn "El servicio no respondió después de 10 intentos."
        warn "Esto puede ser normal si el contenedor aún está iniciando."
        warn "Revisa los logs con: docker logs -f ${CONTAINER_NAME}"
    else
        sleep 2
    fi
done

# Mostrar información
echo ""
echo "=========================================="
info "Despliegue completado!"
echo "=========================================="
echo ""
echo "La aplicación está disponible en:"
if [ "$USE_HOST_NETWORK" = true ]; then
    echo "  - http://localhost:5000"
    echo "  - http://$(hostname -I | awk '{print $1}'):5000"
else
    echo "  - http://localhost:5005"
    echo "  - http://$(hostname -I | awk '{print $1}'):5005"
fi
echo ""
echo "El contenedor se reiniciará automáticamente:"
echo "  - Si se detiene inesperadamente"
echo "  - Si el servidor se reinicia"
echo "  - Si Docker se reinicia"
echo ""
echo "Comandos útiles:"
echo "  Ver logs:        docker logs -f ${CONTAINER_NAME}"
if [ "$USE_HOST_NETWORK" = true ]; then
    echo "  Verificar salud: curl http://localhost:5000/health"
else
    echo "  Verificar salud: curl http://localhost:5005/health"
fi
echo "  Detener:         docker stop ${CONTAINER_NAME}"
echo "  Iniciar:         docker start ${CONTAINER_NAME}"
echo "  Reiniciar:       docker restart ${CONTAINER_NAME}"
echo "  Estado:          docker ps | grep ${CONTAINER_NAME}"
echo "  Stats:           docker stats ${CONTAINER_NAME}"
echo ""

