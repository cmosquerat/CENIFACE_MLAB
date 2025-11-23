# Guía de Debug para Docker - Multilab Agroanalítica

## Verificar Estado del Contenedor

```bash
# Ver contenedores corriendo
docker ps

# Ver todos los contenedores (incluyendo detenidos)
docker ps -a

# Ver información detallada de un contenedor específico
docker inspect multilab-agroanalitica
```

## Ver Logs del Contenedor

```bash
# Ver logs del contenedor
docker logs multilab-agroanalitica

# Ver logs en tiempo real (seguir)
docker logs -f multilab-agroanalitica

# Ver últimas 100 líneas de logs
docker logs --tail 100 multilab-agroanalitica

# Ver logs con timestamp
docker logs -t multilab-agroanalitica
```

## Ejecutar en Modo Interactivo (Debug)

### Opción 1: Ejecutar con shell interactivo

```bash
# Detener contenedor si está corriendo
docker stop multilab-agroanalitica
docker rm multilab-agroanalitica

# Ejecutar en modo interactivo con shell
docker run -it --rm \
  -p 5005:5005 \
  --env-file .env \
  --entrypoint /bin/bash \
  multilab-agroanalitica

# Dentro del contenedor puedes:
# - Verificar variables de entorno: env | grep PORT
# - Verificar archivos: ls -la
# - Ejecutar manualmente: python3 app.py
# - Verificar Chrome: google-chrome --version
```

### Opción 2: Ejecutar con override de comando

```bash
# Ejecutar con shell pero mantener el entrypoint
docker run -it --rm \
  -p 5005:5005 \
  --env-file .env \
  multilab-agroanalitica \
  /bin/bash

# O ejecutar directamente Python con debug
docker run -it --rm \
  -p 5005:5005 \
  --env-file .env \
  multilab-agroanalitica \
  python3 -u app.py
```

### Opción 3: Entrar a un contenedor corriendo

```bash
# Si el contenedor está corriendo, entrar a él
docker exec -it multilab-agroanalitica /bin/bash

# O ejecutar comandos directamente
docker exec multilab-agroanalitica env
docker exec multilab-agroanalitica ls -la /app
docker exec multilab-agroanalitica python3 --version
```

## Verificar Variables de Entorno

```bash
# Ver todas las variables de entorno del contenedor
docker exec multilab-agroanalitica env

# Ver una variable específica
docker exec multilab-agroanalitica sh -c 'echo $PORT'
docker exec multilab-agroanalitica sh -c 'echo $HOST'
```

## Verificar Archivos y Directorios

```bash
# Ver estructura de directorios
docker exec multilab-agroanalitica ls -la /app

# Verificar que los archivos existen
docker exec multilab-agroanalitica test -f /app/app.py && echo "app.py existe"
docker exec multilab-agroanalitica test -f /app/multilab.db && echo "multilab.db existe"
docker exec multilab-agroanalitica test -d /app/templates && echo "templates existe"

# Ver contenido de un archivo
docker exec multilab-agroanalitica cat /app/app.py | head -20
```

## Verificar Dependencias

```bash
# Verificar Chrome
docker exec multilab-agroanalitica google-chrome --version

# Verificar Python
docker exec multilab-agroanalitica python3 --version

# Verificar pip packages
docker exec multilab-agroanalitica pip3 list | grep -i flask

# Verificar que el puerto está escuchando
docker exec multilab-agroanalitica netstat -tlnp | grep 5005
# O con ss
docker exec multilab-agroanalitica ss -tlnp | grep 5005
```

## Ejecutar con Debug Detallado

```bash
# Ejecutar con Python en modo verbose
docker run -it --rm \
  -p 5005:5005 \
  --env-file .env \
  -e DEBUG=True \
  -e PYTHONUNBUFFERED=1 \
  multilab-agroanalitica \
  python3 -u app.py
```

## Script de Debug Rápido

Crea un archivo `debug-docker.sh`:

```bash
#!/bin/bash
CONTAINER_NAME="multilab-agroanalitica"

echo "=== Estado del Contenedor ==="
docker ps -a | grep $CONTAINER_NAME

echo ""
echo "=== Últimos 50 líneas de Logs ==="
docker logs --tail 50 $CONTAINER_NAME

echo ""
echo "=== Variables de Entorno ==="
docker exec $CONTAINER_NAME env | grep -E "PORT|HOST|DEBUG|DB_PATH"

echo ""
echo "=== Verificando Archivos ==="
docker exec $CONTAINER_NAME ls -la /app/ | head -10

echo ""
echo "=== Verificando Dependencias ==="
docker exec $CONTAINER_NAME python3 --version
docker exec $CONTAINER_NAME google-chrome --version 2>/dev/null || echo "Chrome no encontrado"
```

## Comandos Útiles para Troubleshooting

```bash
# Ver uso de recursos
docker stats multilab-agroanalitica

# Ver eventos del contenedor
docker events --filter container=multilab-agroanalitica

# Reiniciar contenedor
docker restart multilab-agroanalitica

# Detener y eliminar contenedor
docker stop multilab-agroanalitica
docker rm multilab-agroanalitica

# Verificar imagen
docker images | grep multilab-agroanalitica

# Inspeccionar imagen
docker inspect multilab-agroanalitica
```

## Ejecutar con Volúmenes para Debug

```bash
# Montar código local para cambios en tiempo real
docker run -it --rm \
  -p 5005:5005 \
  --env-file .env \
  -v $(pwd):/app \
  -e DEBUG=True \
  -e PYTHONUNBUFFERED=1 \
  multilab-agroanalitica \
  python3 -u app.py
```

## Verificar Health Check

```bash
# Ver estado del health check
docker inspect --format='{{json .State.Health}}' multilab-agroanalitica | jq

# O sin jq
docker inspect multilab-agroanalitica | grep -A 10 Health
```

