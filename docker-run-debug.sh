#!/bin/bash
# Ejecutar contenedor en modo debug interactivo

echo "=========================================="
echo "Ejecutando Multilab en modo DEBUG"
echo "=========================================="
echo ""

# Verificar que .env existe
if [ ! -f ".env" ]; then
    echo "ADVERTENCIA: .env no encontrado"
    echo "Creando .env desde env.example..."
    if [ -f "env.example" ]; then
        cp env.example .env
    fi
fi

echo "Ejecutando contenedor en modo interactivo..."
echo "Presiona Ctrl+C para detener"
echo ""

# Ejecutar en modo interactivo con Python unbuffered para ver logs en tiempo real
docker run -it --rm \
  -p 5005:5005 \
  --env-file .env \
  -e DEBUG=True \
  -e PYTHONUNBUFFERED=1 \
  multilab-agroanalitica \
  python3 -u app.py

