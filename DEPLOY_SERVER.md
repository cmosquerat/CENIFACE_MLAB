# Guía de Despliegue en Servidor Linux

Esta guía explica cómo desplegar Multilab Agroanalítica en un servidor Linux usando Docker Compose.

## Requisitos Previos

1. **Servidor Linux** (Ubuntu 20.04+ recomendado)
2. **Acceso SSH** al servidor
3. **Docker y Docker Compose** instalados
4. **Base de datos SQLite** (`multilab.db`) disponible

## Paso 1: Instalar Docker y Docker Compose

### Instalar Docker

```bash
# Actualizar sistema
sudo apt-get update

# Instalar dependencias
sudo apt-get install -y \
    ca-certificates \
    curl \
    gnupg \
    lsb-release

# Agregar clave GPG oficial de Docker
sudo mkdir -p /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg

# Agregar repositorio de Docker
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# Instalar Docker Engine
sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# Agregar usuario actual al grupo docker (para ejecutar sin sudo)
sudo usermod -aG docker $USER

# Verificar instalación
docker --version
docker compose version
```

**Nota:** Después de agregar el usuario al grupo docker, necesitas cerrar sesión y volver a iniciar sesión para que los cambios surtan efecto.

## Paso 2: Preparar el Servidor

### Crear directorio de trabajo

```bash
# Crear directorio para la aplicación
sudo mkdir -p /opt/multilab
sudo chown $USER:$USER /opt/multilab
cd /opt/multilab
```

### Transferir archivos al servidor

Desde tu máquina local, transfiere los archivos necesarios al servidor:

```bash
# Desde tu máquina local (Windows/Mac/Linux)
scp -r \
    Dockerfile \
    docker-compose.yml \
    requirements.txt \
    app.py \
    config.py \
    database.py \
    data_mapper.py \
    siascafe_client.py \
    templates/ \
    static/ \
    multilab.db \
    .env \
    usuario@servidor:/opt/multilab/
```

O usando `rsync` (más eficiente):

```bash
rsync -avz \
    --exclude '*.pyc' \
    --exclude '__pycache__' \
    --exclude '.git' \
    --exclude 'node_modules' \
    ./ usuario@servidor:/opt/multilab/
```

### Crear estructura de directorios

```bash
# En el servidor
cd /opt/multilab
mkdir -p static/pdfs
mkdir -p static/images
chmod 755 static/pdfs
```

## Paso 3: Configurar Variables de Entorno

### Crear archivo `.env`

```bash
cd /opt/multilab
nano .env
```

Contenido del archivo `.env`:

```env
# Configuración del servidor
HOST=0.0.0.0
PORT=5005
DEBUG=False

# Base de datos
DB_PATH=/app/data/multilab.db

# Directorio de PDFs
PDF_STORAGE_DIR=/app/static/pdfs

# SIASCAFE
SIASCAFE_BASE_URL=https://agroclima.cenicafe.org
SIASCAFE_URL=https://agroclima.cenicafe.org/siascafe

# Valores por defecto (opcional)
SIASCAFE_DEFAULT_SOLICITANTE=Default Solicitante
SIASCAFE_DEFAULT_DEPARTAMENTO=Default Departamento
SIASCAFE_DEFAULT_MUNICIPIO=Default Municipio
SIASCAFE_DEFAULT_FINCA=Default Finca
SIASCAFE_DEFAULT_LOTE=Default Lote
```

## Paso 4: Verificar Archivos Necesarios

Asegúrate de tener estos archivos en `/opt/multilab`:

```bash
cd /opt/multilab
ls -la

# Deberías ver:
# - Dockerfile
# - docker-compose.yml
# - requirements.txt
# - app.py
# - config.py
# - database.py
# - data_mapper.py
# - siascafe_client.py
# - templates/
# - static/
# - multilab.db
# - .env
```

## Paso 5: Construir y Ejecutar con Docker Compose

### Construir la imagen

```bash
cd /opt/multilab
docker compose build
```

Este proceso puede tardar varios minutos la primera vez (descarga de dependencias, Chrome, etc.).

### Iniciar el contenedor

```bash
# Iniciar en segundo plano (detached mode)
docker compose up -d

# Ver logs en tiempo real
docker compose logs -f

# Ver solo los últimos logs
docker compose logs --tail=100
```

### Verificar que está funcionando

```bash
# Verificar estado del contenedor
docker compose ps

# Verificar salud del contenedor
docker compose ps --format "table {{.Name}}\t{{.Status}}\t{{.Ports}}"

# Probar endpoint de salud
curl http://localhost:5005/health

# O desde fuera del servidor
curl http://IP_DEL_SERVIDOR:5005/health
```

## Paso 6: Configurar Firewall (si es necesario)

Si el servidor tiene firewall activo, abre el puerto 5005:

```bash
# UFW (Ubuntu)
sudo ufw allow 5005/tcp
sudo ufw reload

# Firewalld (CentOS/RHEL)
sudo firewall-cmd --permanent --add-port=5005/tcp
sudo firewall-cmd --reload
```

## Paso 7: Configurar Nginx como Proxy Reverso (Opcional pero Recomendado)

Para producción, es recomendable usar Nginx como proxy reverso:

### Instalar Nginx

```bash
sudo apt-get update
sudo apt-get install -y nginx
```

### Configurar Nginx

```bash
sudo nano /etc/nginx/sites-available/multilab
```

Contenido:

```nginx
server {
    listen 80;
    server_name tu-dominio.com;  # Cambiar por tu dominio o IP

    location / {
        proxy_pass http://localhost:5005;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Timeouts para operaciones largas
        proxy_connect_timeout 300s;
        proxy_send_timeout 300s;
        proxy_read_timeout 300s;
    }
}
```

### Activar configuración

```bash
sudo ln -s /etc/nginx/sites-available/multilab /etc/nginx/sites-enabled/
sudo nginx -t  # Verificar configuración
sudo systemctl reload nginx
```

## Comandos Útiles

### Gestión del contenedor

```bash
# Detener el contenedor
docker compose down

# Detener y eliminar volúmenes
docker compose down -v

# Reiniciar el contenedor
docker compose restart

# Ver logs en tiempo real
docker compose logs -f

# Ver logs de un servicio específico
docker compose logs -f multilab-web

# Ejecutar comando dentro del contenedor
docker compose exec multilab-web bash

# Ver uso de recursos
docker stats multilab-agroanalitica
```

### Actualizar la aplicación

```bash
cd /opt/multilab

# Detener contenedor
docker compose down

# Actualizar código (transferir nuevos archivos)
# ... transferir archivos ...

# Reconstruir imagen
docker compose build --no-cache

# Iniciar nuevamente
docker compose up -d

# Ver logs
docker compose logs -f
```

### Limpiar recursos Docker

```bash
# Eliminar imágenes no utilizadas
docker image prune -a

# Eliminar contenedores detenidos
docker container prune

# Limpiar todo (¡cuidado!)
docker system prune -a
```

## Monitoreo y Mantenimiento

### Verificar salud del servicio

```bash
# Health check manual
curl http://localhost:5005/health

# Ver logs de errores
docker compose logs | grep ERROR

# Ver uso de memoria
docker stats --no-stream multilab-agroanalitica
```

### Backup de la base de datos

```bash
# Crear backup
cp /opt/multilab/multilab.db /opt/multilab/backups/multilab_$(date +%Y%m%d_%H%M%S).db

# O desde dentro del contenedor
docker compose exec multilab-web cp /app/data/multilab.db /app/data/backup_$(date +%Y%m%d).db
```

### Limpiar PDFs antiguos

```bash
# Eliminar PDFs más antiguos de 7 días
find /opt/multilab/static/pdfs -name "*.pdf" -mtime +7 -delete
```

## Solución de Problemas

### El contenedor no inicia

```bash
# Ver logs detallados
docker compose logs multilab-web

# Verificar configuración
docker compose config

# Verificar que el puerto no esté en uso
sudo netstat -tulpn | grep 5005
```

### Error de permisos

```bash
# Asegurar permisos correctos
sudo chown -R $USER:$USER /opt/multilab
chmod -R 755 /opt/multilab/static/pdfs
```

### Chrome/Selenium no funciona

```bash
# Verificar Chrome dentro del contenedor
docker compose exec multilab-web google-chrome --version
docker compose exec multilab-web chromedriver --version

# Ver logs de Selenium
docker compose logs | grep SELENIUM
```

### Puerto ya en uso

```bash
# Cambiar puerto en docker-compose.yml
# Cambiar "5005:5005" a "5006:5005" (puerto externo:interno)
# Luego reiniciar
docker compose down
docker compose up -d
```

## Acceso a la Aplicación

Una vez desplegado, la aplicación estará disponible en:

- **Directo:** `http://IP_DEL_SERVIDOR:5005`
- **Con Nginx:** `http://tu-dominio.com` o `http://IP_DEL_SERVIDOR`

## Próximos Pasos

1. Configurar SSL/HTTPS con Let's Encrypt (recomendado para producción)
2. Configurar monitoreo (Prometheus, Grafana)
3. Configurar backups automáticos de la base de datos
4. Configurar log rotation para los logs de Docker

