#!/bin/bash

# Script para actualizar aplicación sin rebuild completo
# Solo copia archivos nuevos y reinicia el contenedor
# Uso: ./update-without-rebuild.sh

set -e

CONTAINER_NAME="multilab-agroanalitica"

echo "=========================================="
echo "Actualización sin Rebuild"
echo "=========================================="
echo ""

# Verificar que el contenedor existe y está corriendo
if ! docker ps --format "{{.Names}}" | grep -q "^${CONTAINER_NAME}$"; then
    echo "[ERROR] Contenedor ${CONTAINER_NAME} no está corriendo"
    echo "Ejecuta primero: docker run ... (ver docker-run-linux.sh)"
    exit 1
fi

echo "[INFO] Contenedor encontrado: ${CONTAINER_NAME}"
echo ""

# Lista de archivos a copiar (solo código Python y templates/static)
FILES_TO_COPY=(
    "app.py"
    "config.py"
    "database.py"
    "data_mapper.py"
    "siascafe_client.py"
    "templates/"
    "static/"
    ".env"
)

echo "[INFO] Copiando archivos actualizados al contenedor..."
for file in "${FILES_TO_COPY[@]}"; do
    if [ -e "$file" ]; then
        echo "  Copiando: $file"
        # Si es un directorio, copiar recursivamente
        if [ -d "$file" ]; then
            docker cp "$file/." "${CONTAINER_NAME}:/app/$file/"
        else
            docker cp "$file" "${CONTAINER_NAME}:/app/"
        fi
    else
        echo "  [WARN] Archivo no encontrado: $file"
    fi
done

# Forzar recarga de variables de entorno copiando .env
if [ -f ".env" ]; then
    echo "  [INFO] Forzando recarga de .env..."
    docker cp ".env" "${CONTAINER_NAME}:/app/.env"
fi

echo ""
echo "[INFO] Reiniciando contenedor para aplicar cambios..."
docker restart ${CONTAINER_NAME}

echo ""
echo "[INFO] Esperando a que el contenedor inicie..."
sleep 5

# Verificar salud
echo "[INFO] Verificando salud del servicio..."
for i in {1..10}; do
    if curl -f http://localhost:5005/health &> /dev/null 2>&1; then
        echo "[OK] Servicio está funcionando correctamente"
        break
    fi
    if [ $i -eq 10 ]; then
        echo "[WARN] El servicio no respondió. Revisa los logs:"
        echo "  docker logs ${CONTAINER_NAME}"
    else
        sleep 2
    fi
done

echo ""
echo "=========================================="
echo "[OK] Actualización completada"
echo "=========================================="
echo ""
echo "Ver logs: docker logs -f ${CONTAINER_NAME}"
echo ""

