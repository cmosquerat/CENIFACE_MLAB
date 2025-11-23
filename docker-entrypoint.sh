#!/bin/bash
# No usar set -e aquí porque queremos manejar errores manualmente

echo "=========================================="
echo "Iniciando Multilab Agroanalítica"
echo "=========================================="

# Nota: Las variables de entorno se cargan automáticamente desde .env
# mediante docker-compose (env_file) o se pueden pasar como variables de entorno.
# No es necesario cargar manualmente aquí para evitar problemas con BOM y caracteres especiales.

# Verificar que la base de datos existe
if [ ! -f "multilab.db" ] && [ ! -f "data/multilab.db" ]; then
    echo "ADVERTENCIA: multilab.db no encontrado"
    echo "Algunas funcionalidades pueden no estar disponibles"
fi

# Verificar que Chrome está instalado
if ! command -v google-chrome &> /dev/null; then
    echo "ERROR: Google Chrome no está instalado"
    exit 1
fi

echo "Chrome versión: $(google-chrome --version 2>/dev/null || echo 'N/A')"
echo "Python versión: $(python3 --version 2>/dev/null || echo 'N/A')"
echo "Puerto: ${PORT:-5005}"
echo "Host: ${HOST:-0.0.0.0}"
echo "=========================================="

# Ejecutar la aplicación
set -e  # Activar set -e solo para la ejecución final
exec "$@"

