# Instalación en Servidor Linux sin Entorno Gráfico

Este documento describe cómo instalar y ejecutar el sistema SIASCAFE en un servidor Linux sin entorno gráfico (headless).

## Requisitos del Sistema

- Linux (Ubuntu/Debian recomendado)
- Python 3.8 o superior
- Acceso a internet para descargar dependencias

## Instalación

### 1. Instalar Chrome/Chromium y dependencias

```bash
# Actualizar sistema
sudo apt-get update

# Instalar Chrome
wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
sudo apt-get install -y ./google-chrome-stable_current_amd64.deb

# O instalar Chromium (alternativa más ligera)
sudo apt-get install -y chromium-browser chromium-chromedriver

# Instalar dependencias necesarias para Chrome headless
sudo apt-get install -y \
    libnss3 \
    libatk-bridge2.0-0 \
    libdrm2 \
    libxkbcommon0 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxrandr2 \
    libgbm1 \
    libasound2 \
    libpango-1.0-0 \
    libcairo2 \
    libatk1.0-0 \
    libatspi2.0-0 \
    libgtk-3-0
```

### 2. Instalar Python y dependencias

```bash
# Instalar Python y pip si no están instalados
sudo apt-get install -y python3 python3-pip python3-venv

# Crear entorno virtual
python3 -m venv venv
source venv/bin/activate

# Instalar dependencias
pip install -r requirements.txt
```

### 3. Configurar base de datos SQLite

```bash
# Asegurarse de que el archivo multilab.db existe
# Si no existe, ejecutar los scripts de conversión:
python convert_mysql_to_sqlite.py
python setup_catalogos_sqlite.py
```

### 4. Configurar permisos y directorios

```bash
# Crear directorio para PDFs temporales
sudo mkdir -p /tmp/siascafe_pdfs
sudo chmod 777 /tmp/siascafe_pdfs

# Asegurar permisos de escritura en el directorio del proyecto
chmod -R 755 /ruta/al/proyecto
```

## Ejecución

### Modo Headless (recomendado para servidor)

```bash
# Activar entorno virtual
source venv/bin/activate

# Ejecutar en modo headless
python test_selenium_sqlite.py 11000 CRECIMIENTO 1 4444 0 2025 --headless
```

### Ejecutar como servicio (systemd)

Crear archivo `/etc/systemd/system/siascafe.service`:

```ini
[Unit]
Description=SIASCAFE PDF Generator Service
After=network.target

[Service]
Type=simple
User=tu_usuario
WorkingDirectory=/ruta/al/proyecto
Environment="PATH=/ruta/al/proyecto/venv/bin"
ExecStart=/ruta/al/proyecto/venv/bin/python test_selenium_sqlite.py 11000 CRECIMIENTO 1 4444 0 2025 --headless
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Activar el servicio:
```bash
sudo systemctl daemon-reload
sudo systemctl enable siascafe.service
sudo systemctl start siascafe.service
```

## Verificación

### Verificar que Chrome funciona en modo headless

```bash
google-chrome --headless --disable-gpu --dump-dom https://www.google.com
```

O con Chromium:
```bash
chromium-browser --headless --disable-gpu --dump-dom https://www.google.com
```

### Verificar logs

```bash
# Ver logs del servicio
sudo journalctl -u siascafe.service -f

# Ver logs del script directamente
python test_selenium_sqlite.py 11000 CRECIMIENTO 1 4444 0 2025 --headless 2>&1 | tee siascafe.log
```

## Solución de Problemas

### Error: "ChromeDriver not found"
- Verificar que ChromeDriver está instalado: `which chromedriver`
- Si no está, `webdriver-manager` lo descargará automáticamente

### Error: "No display" o "cannot connect to X server"
- Asegurarse de usar `--headless` en el comando
- Verificar que las opciones headless están activadas en el código

### Error: "Permission denied" en /tmp/siascafe_pdfs
```bash
sudo chmod 777 /tmp/siascafe_pdfs
```

### Chrome se cuelga o consume mucha memoria
- El código ya incluye `--single-process` para reducir uso de memoria
- Considerar aumentar el timeout en `_wait_for_pdf()` si el servidor es lento

### PDF no se descarga
- Verificar permisos de escritura en `/tmp/siascafe_pdfs`
- Verificar logs para ver si el botón "Descargar PDF" se encuentra correctamente
- Aumentar timeout si el servidor es lento: modificar `timeout` en `_wait_for_pdf()`

## Notas Importantes

1. **Recursos del servidor**: Chrome headless consume memoria. Asegúrate de tener al menos 2GB de RAM disponible.

2. **Sin entorno gráfico**: El código está configurado para funcionar sin X11 ni display. Las opciones `--headless`, `--no-sandbox`, y `--disable-gpu` son esenciales.

3. **Seguridad**: En producción, considera ejecutar Chrome con un usuario sin privilegios y limitar permisos del sistema.

4. **Timeouts**: Los timeouts están configurados para 60 segundos. Si tu servidor es más lento, puedes aumentarlos en `siascafe_client.py`.

## Comandos Útiles

```bash
# Ver procesos de Chrome
ps aux | grep chrome

# Matar procesos de Chrome colgados
pkill -9 chrome

# Ver uso de memoria
free -h

# Ver espacio en disco
df -h
```

