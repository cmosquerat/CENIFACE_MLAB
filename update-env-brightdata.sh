#!/bin/bash

# Script para actualizar .env con configuración de Bright Data
# Uso: ./update-env-brightdata.sh

echo "=========================================="
echo "Actualizando .env con Bright Data Proxy"
echo "=========================================="
echo ""

ENV_FILE=".env"
BRIGHT_DATA_PROXY="SIASCAFE_PROXY_URL=http://brd-customer-hl_6ad5dde5-zone-datacenter_proxy1:vekb114yzhdx@brd.superproxy.io:33335"

# Verificar si .env existe
if [ ! -f "$ENV_FILE" ]; then
    echo "[INFO] Archivo .env no existe. Creando desde env.example..."
    if [ -f "env.example" ]; then
        cp env.example .env
        echo "[OK] Archivo .env creado"
    else
        echo "[ERROR] No se encontró env.example"
        exit 1
    fi
fi

# Verificar si ya existe configuración de proxy
if grep -q "SIASCAFE_PROXY_URL" "$ENV_FILE"; then
    echo "[INFO] Reemplazando configuración de proxy existente..."
    # Reemplazar línea existente
    sed -i.bak "s|SIASCAFE_PROXY_URL=.*|$BRIGHT_DATA_PROXY|" "$ENV_FILE"
    # Eliminar líneas comentadas relacionadas
    sed -i.bak '/^#.*SIASCAFE_PROXY/d' "$ENV_FILE"
    sed -i.bak '/^SIASCAFE_PROXY_HOST=/d' "$ENV_FILE"
    sed -i.bak '/^SIASCAFE_PROXY_PORT=/d' "$ENV_FILE"
    sed -i.bak '/^SIASCAFE_PROXY_USER=/d' "$ENV_FILE"
    sed -i.bak '/^SIASCAFE_PROXY_PASS=/d' "$ENV_FILE"
    rm -f "${ENV_FILE}.bak"
else
    echo "[INFO] Agregando configuración de proxy..."
    # Agregar después de SIASCAFE_URL
    if grep -q "SIASCAFE_URL=" "$ENV_FILE"; then
        sed -i.bak "/SIASCAFE_URL=.*/a\\
\\
# Bright Data Proxy (para evitar bloqueos geográficos)\\
$BRIGHT_DATA_PROXY" "$ENV_FILE"
        rm -f "${ENV_FILE}.bak"
    else
        # Agregar al final
        echo "" >> "$ENV_FILE"
        echo "# Bright Data Proxy (para evitar bloqueos geográficos)" >> "$ENV_FILE"
        echo "$BRIGHT_DATA_PROXY" >> "$ENV_FILE"
    fi
fi

echo "[OK] Archivo .env actualizado con Bright Data Proxy"
echo ""
echo "Configuración agregada:"
echo "  $BRIGHT_DATA_PROXY"
echo ""
echo "Próximos pasos:"
echo "  1. Reinicia el contenedor Docker:"
echo "     docker restart multilab-agroanalitica"
echo "  2. Verifica los logs:"
echo "     docker logs multilab-agroanalitica | grep PROXY"
echo ""

