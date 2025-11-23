# Docker - Multilab Agroanalítica

Guía para ejecutar la aplicación en Docker con Ubuntu (sin entorno gráfico).

## Requisitos

- Docker instalado
- Docker Compose (opcional pero recomendado)
- Archivo `.env` configurado (ver `.env.example`)

## Inicio Rápido

### Linux/Mac

```bash
chmod +x docker-start.sh
./docker-start.sh
```

Este script:
- Verifica dependencias (Docker, Docker Compose)
- Crea `.env` desde `env.example` si no existe
- Construye la imagen Docker
- Inicia el contenedor
- Verifica que el servidor esté funcionando

### Windows

```powershell
# Crear .env si no existe
if (!(Test-Path .env)) { Copy-Item env.example .env }

# Construir e iniciar
docker-compose build
docker-compose up -d
```

## Configuración Inicial

1. **Crear archivo `.env`** (si no se creó automáticamente):
```bash
cp env.example .env
```

2. **Editar `.env`** según tus necesidades:
```env
HOST=0.0.0.0
PORT=5005
DEBUG=False
DB_PATH=multilab.db
```

## Construcción de la Imagen

### Opción 1: Usando Docker Compose (Recomendado)

```bash
docker-compose build
```

### Opción 2: Usando Docker directamente

```bash
docker build -t multilab-agroanalitica .
```

## Ejecución

### Opción 1: Usando Docker Compose

```bash
docker-compose up -d
```

Para ver los logs:
```bash
docker-compose logs -f
```

Para detener:
```bash
docker-compose down
```

### Opción 2: Usando Docker directamente

```bash
docker run -d \
  --name multilab-agroanalitica \
  -p 5005:5005 \
  --env-file .env \
  -v $(pwd)/multilab.db:/app/multilab.db:ro \
  -v $(pwd)/static/pdfs:/app/static/pdfs \
  multilab-agroanalitica
```

## Verificación

1. **Verificar que el contenedor está corriendo**:
```bash
docker ps
```

2. **Verificar logs**:
```bash
docker logs multilab-agroanalitica
```

3. **Probar endpoint de salud**:
```bash
curl http://localhost:5005/health
```

4. **Abrir en navegador**:
```
http://localhost:5005
```

## Solución de Problemas

### Error: Chrome no se inicia

Verifica los logs del contenedor:
```bash
docker logs multilab-agroanalitica
```

### Error: Base de datos no encontrada

Asegúrate de que `multilab.db` existe y está montado correctamente:
```bash
ls -la multilab.db
```

### Error: Permisos

Si hay problemas de permisos, verifica que los volúmenes estén montados correctamente:
```bash
docker exec multilab-agroanalitica ls -la /app/multilab.db
```

### Reconstruir imagen

Si necesitas reconstruir la imagen después de cambios:
```bash
docker-compose build --no-cache
docker-compose up -d
```

## Características

- ✅ Ubuntu 22.04 como base
- ✅ Google Chrome instalado para Selenium
- ✅ ChromeDriver configurado automáticamente
- ✅ Modo headless (sin entorno gráfico)
- ✅ Variables de entorno desde `.env`
- ✅ Volúmenes para persistencia de datos
- ✅ Health check configurado
- ✅ Usuario no-root para seguridad

## Puertos

- **5005**: Puerto HTTP de la aplicación web

## Volúmenes

- `./multilab.db` → `/app/multilab.db` (base de datos, solo lectura)
- `./static/pdfs` → `/app/static/pdfs` (PDFs generados)
- `./.env` → `/app/.env` (variables de entorno)

## Comandos Útiles

```bash
# Ver logs en tiempo real
docker-compose logs -f

# Ejecutar comando en el contenedor
docker exec -it multilab-agroanalitica bash

# Reiniciar contenedor
docker-compose restart

# Detener y eliminar contenedor
docker-compose down

# Ver uso de recursos
docker stats multilab-agroanalitica
```

