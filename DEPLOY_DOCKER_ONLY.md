# Despliegue con Docker (sin Docker Compose)

Guía para desplegar Multilab Agroanalítica usando solo Docker, con reinicio automático.

## Requisitos Previos

1. **Docker instalado** en el servidor
2. **Base de datos SQLite** (`multilab.db`) disponible

## Paso 1: Instalar Docker (si no está instalado)

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
sudo apt-get install -y docker-ce docker-ce-cli containerd.io

# Agregar usuario actual al grupo docker
sudo usermod -aG docker $USER

# Verificar instalación
docker --version
```

**Nota:** Después de agregar el usuario al grupo docker, cierra sesión y vuelve a iniciar sesión.

## Paso 2: Preparar el Servidor

### Crear directorio de trabajo

```bash
sudo mkdir -p /opt/multilab
sudo chown $USER:$USER /opt/multilab
cd /opt/multilab
```

### Transferir archivos al servidor

Desde tu máquina local:

```bash
# Transferir archivos necesarios
scp -r \
    Dockerfile \
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

O usando `rsync`:

```bash
rsync -avz \
    --exclude '*.pyc' \
    --exclude '__pycache__' \
    --exclude '.git' \
    --exclude 'node_modules' \
    --exclude 'docker-compose.yml' \
    --exclude 'deploy.sh' \
    ./ usuario@servidor:/opt/multilab/
```

### Crear estructura de directorios

```bash
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
PORT=5000
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

## Paso 4: Construir la Imagen Docker

```bash
cd /opt/multilab

# Construir la imagen
docker build -t multilab-agroanalitica:latest .

# Verificar que la imagen se creó
docker images | grep multilab-agroanalitica
```

Este proceso puede tardar varios minutos la primera vez.

## Paso 5: Ejecutar el Contenedor con Reinicio Automático

### Opción 1: Comando Completo (Recomendado)

```bash
docker run -d \
  --name multilab-agroanalitica \
  --restart=unless-stopped \
  -p 5000:5000 \
  --env-file .env \
  -v $(pwd)/multilab.db:/app/multilab.db:ro \
  -v $(pwd)/static/pdfs:/app/static/pdfs \
  multilab-agroanalitica:latest
```

### Opción 2: Con más opciones de persistencia

```bash
docker run -d \
  --name multilab-agroanalitica \
  --restart=unless-stopped \
  -p 5000:5000 \
  --env-file .env \
  -v /opt/multilab/multilab.db:/app/multilab.db:ro \
  -v /opt/multilab/static/pdfs:/app/static/pdfs \
  --memory=2g \
  --memory-swap=2g \
  --cpus="2.0" \
  multilab-agroanalitica:latest
```

### Explicación de las opciones:

- `-d`: Ejecutar en segundo plano (detached)
- `--name multilab-agroanalitica`: Nombre del contenedor
- `--restart=unless-stopped`: Reiniciar automáticamente siempre, excepto si se detiene manualmente
- `-p 5000:5000`: Mapear puerto 5000 del host al puerto 5000 del contenedor
- `--env-file .env`: Cargar variables de entorno desde archivo
- `-v $(pwd)/multilab.db:/app/multilab.db:ro`: Montar base de datos (solo lectura)
- `-v $(pwd)/static/pdfs:/app/static/pdfs`: Montar directorio de PDFs
- `--memory=2g`: Límite de memoria
- `--cpus="2.0"`: Límite de CPUs

## Paso 6: Verificar que Funciona

```bash
# Ver estado del contenedor
docker ps | grep multilab-agroanalitica

# Ver logs
docker logs multilab-agroanalitica

# Ver logs en tiempo real
docker logs -f multilab-agroanalitica

# Probar endpoint de salud
curl http://localhost:5000/health

# O desde fuera del servidor
curl http://IP_DEL_SERVIDOR:5000/health
```

## Paso 7: Configurar Firewall (si es necesario)

```bash
# UFW (Ubuntu)
sudo ufw allow 5000/tcp
sudo ufw reload

# Firewalld (CentOS/RHEL)
sudo firewall-cmd --permanent --add-port=5000/tcp
sudo firewall-cmd --reload
```

## Comandos Útiles

### Gestión del contenedor

```bash
# Detener el contenedor
docker stop multilab-agroanalitica

# Iniciar el contenedor
docker start multilab-agroanalitica

# Reiniciar el contenedor
docker restart multilab-agroanalitica

# Ver logs
docker logs multilab-agroanalitica

# Ver logs en tiempo real
docker logs -f multilab-agroanalitica

# Ver últimas 100 líneas de logs
docker logs --tail=100 multilab-agroanalitica

# Ejecutar comando dentro del contenedor
docker exec -it multilab-agroanalitica bash

# Ver uso de recursos
docker stats multilab-agroanalitica

# Ver información del contenedor
docker inspect multilab-agroanalitica
```

### Actualizar la aplicación

```bash
cd /opt/multilab

# Detener contenedor
docker stop multilab-agroanalitica

# Eliminar contenedor (los datos en volúmenes se mantienen)
docker rm multilab-agroanalitica

# Actualizar código (transferir nuevos archivos)
# ... transferir archivos ...

# Reconstruir imagen
docker build -t multilab-agroanalitica:latest .

# Ejecutar nuevamente con el mismo comando
docker run -d \
  --name multilab-agroanalitica \
  --restart=unless-stopped \
  -p 5000:5000 \
  --env-file .env \
  -v $(pwd)/multilab.db:/app/multilab.db:ro \
  -v $(pwd)/static/pdfs:/app/static/pdfs \
  multilab-agroanalitica:latest
```

### Eliminar contenedor e imagen

```bash
# Detener y eliminar contenedor
docker stop multilab-agroanalitica
docker rm multilab-agroanalitica

# Eliminar imagen
docker rmi multilab-agroanalitica:latest
```

## Configurar como Servicio del Sistema (systemd) - Opcional

Para mayor control, puedes crear un servicio systemd:

### Crear archivo de servicio

```bash
sudo nano /etc/systemd/system/multilab.service
```

Contenido:

```ini
[Unit]
Description=Multilab Agroanalitica Docker Container
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/opt/multilab
ExecStart=/usr/bin/docker start multilab-agroanalitica
ExecStop=/usr/bin/docker stop multilab-agroanalitica
TimeoutStartSec=0
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### Activar servicio

```bash
# Recargar systemd
sudo systemctl daemon-reload

# Habilitar servicio (inicia automáticamente al arrancar)
sudo systemctl enable multilab.service

# Iniciar servicio
sudo systemctl start multilab.service

# Ver estado
sudo systemctl status multilab.service
```

## Verificar Reinicio Automático

### Probar reinicio automático

```bash
# Simular fallo del contenedor
docker kill multilab-agroanalitica

# Esperar unos segundos y verificar que se reinició
docker ps | grep multilab-agroanalitica

# Ver logs para confirmar reinicio
docker logs --tail=50 multilab-agroanalitica
```

### Verificar que inicia al arrancar el servidor

```bash
# Reiniciar el servidor
sudo reboot

# Después de reiniciar, verificar que el contenedor está corriendo
docker ps | grep multilab-agroanalitica
```

## Monitoreo

### Ver logs en tiempo real

```bash
docker logs -f multilab-agroanalitica
```

### Ver uso de recursos

```bash
docker stats multilab-agroanalitica --no-stream
```

### Verificar salud del servicio

```bash
# Crear script de monitoreo
cat > /opt/multilab/health-check.sh << 'EOF'
#!/bin/bash
if ! curl -f http://localhost:5000/health &> /dev/null; then
    echo "Servicio no responde, reiniciando..."
    docker restart multilab-agroanalitica
fi
EOF

chmod +x /opt/multilab/health-check.sh

# Agregar a crontab para verificar cada 5 minutos
(crontab -l 2>/dev/null; echo "*/5 * * * * /opt/multilab/health-check.sh") | crontab -
```

## Solución de Problemas

### El contenedor no inicia

```bash
# Ver logs detallados
docker logs multilab-agroanalitica

# Verificar configuración
docker inspect multilab-agroanalitica

# Verificar que el puerto no esté en uso
sudo netstat -tulpn | grep 5000
```

### El contenedor se detiene constantemente

```bash
# Ver logs para identificar el error
docker logs multilab-agroanalitica

# Verificar recursos del sistema
docker stats multilab-agroanalitica

# Verificar espacio en disco
df -h
```

### Error de permisos

```bash
# Asegurar permisos correctos
sudo chown -R $USER:$USER /opt/multilab
chmod -R 755 /opt/multilab/static/pdfs
```

### Verificar que el reinicio automático está activo

```bash
# Ver política de reinicio del contenedor
docker inspect multilab-agroanalitica | grep -A 5 RestartPolicy
```

Debería mostrar:
```json
"RestartPolicy": {
    "Name": "unless-stopped",
    "MaximumRetryCount": 0
}
```

## Acceso a la Aplicación

Una vez desplegado, la aplicación estará disponible en:

- `http://IP_DEL_SERVIDOR:5000`

El contenedor se reiniciará automáticamente:
- Si se detiene inesperadamente
- Si el servidor se reinicia
- Si Docker se reinicia

