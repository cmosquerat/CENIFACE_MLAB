# Checklist de Producción

## ✅ Cambios Realizados para Producción

### 1. Configuración de Proxy (Bright Data)
- ✅ Soporte para proxy HTTP con autenticación
- ✅ Configuración en `.env` con `SIASCAFE_PROXY_URL`
- ✅ Logs seguros (oculta contraseña)

### 2. Puertos
- ✅ Puerto interno: 5000 (dentro del contenedor)
- ✅ Puerto externo: 5005 (Windows) o 5005 (Linux)
- ✅ Dockerfile actualizado con PORT=5000

### 3. Logs Filtrados
- ✅ Filtrados logs de `/api/logs`
- ✅ Filtrados logs de `/health`
- ✅ Filtrados logs de `/api/status`

### 4. Configuración de Producción
- ✅ DEBUG=False por defecto
- ✅ HOST=0.0.0.0 para aceptar conexiones externas
- ✅ FLASK_ENV=production en Dockerfile

### 5. Scripts de Despliegue
- ✅ `docker-run-linux.sh` - Despliegue en Linux
- ✅ `docker-run-fast.ps1` - Despliegue rápido Windows
- ✅ `update-without-rebuild.sh` - Actualización sin rebuild
- ✅ `update-without-rebuild.ps1` - Actualización sin rebuild (Windows)

## 📋 Configuración Requerida en `.env`

```env
# Servidor
HOST=0.0.0.0
PORT=5000
DEBUG=False

# Base de datos
DB_PATH=multilab.db

# SIASCAFE
SIASCAFE_BASE_URL=https://agroclima.cenicafe.org
SIASCAFE_URL=https://agroclima.cenicafe.org/siascafe

# Bright Data Proxy (OBLIGATORIO para producción)
SIASCAFE_PROXY_URL=http://brd-customer-hl_6ad5dde5-zone-datacenter_proxy1:vekb114yzhdx@brd.superproxy.io:33335

# Directorios
PDF_STORAGE_DIR=/tmp/siascafe_pdfs
```

## 🚀 Despliegue en Producción

### Opción 1: Despliegue Inicial (con build)

```bash
# Linux
./docker-run-linux.sh

# Windows
.\docker-run-fast.ps1
```

### Opción 2: Actualización Sin Rebuild

```bash
# Linux
./update-without-rebuild.sh

# Windows
.\update-without-rebuild.ps1
```

## 🔄 Actualizar Código Sin Rebuild

El script `update-without-rebuild` copia solo los archivos necesarios:
- `app.py`
- `config.py`
- `database.py`
- `data_mapper.py`
- `siascafe_client.py`
- `templates/`
- `static/`
- `.env`

Y reinicia el contenedor sin necesidad de rebuild completo.

## ⚠️ Cuándo Hacer Rebuild

Solo necesitas rebuild si:
- Cambias `requirements.txt`
- Cambias `Dockerfile`
- Cambias estructura de directorios
- Primera vez que despliegas

## 📝 Verificación Post-Despliegue

```bash
# Verificar que está corriendo
docker ps | grep multilab-agroanalitica

# Verificar salud
curl http://localhost:5005/health

# Ver logs
docker logs -f multilab-agroanalitica

# Verificar proxy configurado
docker logs multilab-agroanalitica | grep PROXY
```

## 🔐 Seguridad

- ✅ Contraseñas ocultas en logs
- ✅ Usuario no-root en contenedor
- ✅ Variables sensibles en `.env` (no en código)
- ✅ `.env` en `.gitignore`

## 📊 Monitoreo

- Health check endpoint: `/health`
- Logs disponibles en: `docker logs`
- Logs web en: `/api/logs` (terminal en UI)

