#!/bin/bash

# Script de despliegue rápido para Multilab Agroanalítica
# Uso: ./deploy.sh

set -e  # Salir si hay algún error

echo "=========================================="
echo "Despliegue de Multilab Agroanalítica"
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
if [ ! -f "docker-compose.yml" ]; then
    error "No se encontró docker-compose.yml. Ejecuta este script desde el directorio raíz del proyecto."
fi

# Verificar Docker
if ! command -v docker &> /dev/null; then
    error "Docker no está instalado. Por favor instálalo primero."
fi

# Verificar Docker Compose
if ! command -v docker compose &> /dev/null && ! command -v docker-compose &> /dev/null; then
    error "Docker Compose no está instalado. Por favor instálalo primero."
fi

info "Docker y Docker Compose encontrados"

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

# Construir imagen
info "Construyendo imagen Docker (esto puede tardar varios minutos)..."
docker compose build

if [ $? -ne 0 ]; then
    error "Error al construir la imagen Docker."
fi

info "Imagen construida exitosamente"

# Detener contenedores existentes
info "Deteniendo contenedores existentes (si existen)..."
docker compose down 2>/dev/null || true

# Iniciar contenedores
info "Iniciando contenedores..."
docker compose up -d

if [ $? -ne 0 ]; then
    error "Error al iniciar los contenedores."
fi

# Esperar a que el contenedor esté listo
info "Esperando a que el servicio esté listo..."
sleep 5

# Verificar salud del servicio
info "Verificando salud del servicio..."
for i in {1..30}; do
    if curl -f http://localhost:5005/health &> /dev/null; then
        info "Servicio está funcionando correctamente!"
        break
    fi
    if [ $i -eq 30 ]; then
        warn "El servicio no respondió después de 30 intentos."
        warn "Revisa los logs con: docker compose logs -f"
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
echo "  - http://localhost:5005"
echo ""
echo "Comandos útiles:"
echo "  Ver logs:        docker compose logs -f"
echo "  Detener:         docker compose down"
echo "  Reiniciar:       docker compose restart"
echo "  Estado:          docker compose ps"
echo ""

