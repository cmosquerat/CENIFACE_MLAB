# Backend SIASCAFE - Generación Automática de PDFs

Backend Flask que genera PDFs de análisis de suelos desde la base de datos multilab usando Selenium para automatizar SIASCAFE.

## Características

- ✅ **100% Automático**: Usa Selenium para llenar formularios y descargar PDFs
- ✅ **Linux Headless**: Funciona en servidores Linux sin desktop
- ✅ **Base de Datos SQLite**: Simple y portable
- ✅ **API REST**: Endpoint simple para generar PDFs

## Requisitos

### Linux (Servidor)

```bash
# Instalar Chrome
sudo apt-get update
sudo apt-get install -y google-chrome-stable

# O para CentOS/RHEL:
sudo yum install -y google-chrome-stable
```

### Python

```bash
pip install -r requirements.txt
```

## Instalación Rápida

```bash
# 1. Crear base de datos SQLite (si no existe)
python convert_mysql_to_sqlite.py

# 2. Instalar dependencias
pip install -r requirements.txt

# 3. Ejecutar servidor
python app.py
```

## Uso

### Generar PDF

```bash
POST http://localhost:5000/api/generate-pdf
Content-Type: application/json

{
  "codigo_lab": 10766,
  "etapa": 0,
  "edad": 0,
  "densidad": 4444,
  "sombrío": 0
}
```

### Ejemplo con curl

```bash
curl -X POST http://localhost:5000/api/generate-pdf \
  -H "Content-Type: application/json" \
  -d '{
    "codigo_lab": 10766,
    "etapa": 0,
    "edad": 0,
    "densidad": 4444,
    "sombrío": 0
  }' \
  --output resultado.pdf
```

## Ejecutar en Background (Linux)

```bash
# Con nohup
nohup python app.py > app.log 2>&1 &

# O con systemd (crear servicio)
sudo systemctl start siascafe-backend
```

## Estructura del Proyecto

```
.
├── app.py                 # Servidor Flask principal
├── config.py             # Configuración
├── database.py           # Acceso a base de datos SQLite
├── data_mapper.py        # Mapeo de datos BD -> SIASCAFE
├── siascafe_client.py    # Cliente Selenium para SIASCAFE
├── test_api.py           # Script de prueba
├── requirements.txt      # Dependencias Python
├── multilab.db           # Base de datos SQLite
└── README.md             # Este archivo
```

## Configuración

Variables de entorno (opcional, en `.env`):

```env
DB_PATH=multilab.db
HOST=0.0.0.0
PORT=5000
PDF_STORAGE_DIR=/tmp/siascafe_pdfs
```

## Testing

```bash
python test_api.py 10766 CRECIMIENTO 0 4444 0
```

## Notas

- El sistema usa Selenium en modo headless para Linux
- ChromeDriver se descarga automáticamente
- Los PDFs se generan automáticamente llenando el formulario web
- Compatible con servidores Linux sin interfaz gráfica
