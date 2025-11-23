# Multilab Agroanalítica - Procesamiento Web de Análisis SIASCAFE

Aplicación web para procesamiento masivo de análisis de suelos usando SIASCAFE.

## Características

- ✅ Interfaz web con identidad de marca Multilab
- ✅ Tabla editable tipo Excel para ingresar múltiples análisis
- ✅ Validación de datos (especialmente ETAPA)
- ✅ Procesamiento en bulk usando Selenium
- ✅ Descarga individual y masiva de PDFs generados
- ✅ Selección de año del análisis

## Requisitos

- Python 3.8+
- Chrome/Chromium instalado
- Base de datos SQLite (`multilab.db`)

## Instalación

1. Instalar dependencias:
```bash
pip install -r requirements.txt
```

2. Asegurarse de que existe la base de datos `multilab.db` en el directorio raíz.

## Uso

1. Iniciar el servidor:
```bash
python app.py
```

2. Abrir el navegador en: `http://localhost:5000`

3. En la interfaz web:
   - Seleccionar el año del análisis
   - Agregar filas con los datos de los análisis:
     - **No. Lab**: Código de laboratorio
     - **ETAPA**: CRECIMIENTO, ZOCA o PRODUCCION (validado)
     - **EDAD M**: Edad en meses (0-1200)
     - **DENSIDAD**: Densidad de siembra (2000-20000)
     - **SOMBRIO**: Porcentaje de sombrío (0-100)
   - Hacer clic en "Procesar Análisis"
   - Esperar a que se completen los análisis
   - Descargar PDFs individuales o todos en ZIP

## Estructura de Archivos

```
.
├── app.py                      # Aplicación Flask principal
├── templates/
│   └── index.html             # Interfaz web
├── static/
│   ├── css/
│   │   └── style.css          # Estilos Multilab
│   ├── js/
│   │   └── app.js             # Lógica JavaScript
│   ├── images/
│   │   └── logo.png           # Logo Multilab
│   └── pdfs/                  # PDFs generados (se crea automáticamente)
├── database.py                # Manejo de BD
├── data_mapper.py             # Mapeo de datos
├── siascafe_client.py         # Cliente Selenium
└── multilab.db                # Base de datos SQLite
```

## API Endpoints

- `GET /` - Página principal
- `POST /api/process` - Procesar análisis en bulk
- `GET /api/status/<job_id>` - Obtener estado de procesamiento
- `GET /api/download/<filename>` - Descargar PDF individual
- `GET /api/download-all/<job_id>` - Descargar todos los PDFs como ZIP

## Notas

- El procesamiento se realiza en modo headless (sin ventana visible del navegador)
- Los PDFs se guardan temporalmente en `static/pdfs/`
- El procesamiento puede tardar varios segundos por análisis
- Se recomienda procesar en lotes pequeños para evitar timeouts

## Solución de Problemas

**Error: Chrome no se inicia**
- Asegúrate de tener Chrome/Chromium instalado
- En Linux, puede requerir: `sudo apt-get install google-chrome-stable`

**Error: Base de datos no encontrada**
- Verifica que `multilab.db` existe en el directorio raíz
- Ejecuta `setup_catalogos_sqlite.py` si es necesario

**Error: No se encuentra muestra**
- Verifica que el código de laboratorio existe en la BD
- Verifica que el año seleccionado es correcto

