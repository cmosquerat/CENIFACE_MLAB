#!/usr/bin/env python
"""
Aplicación web Flask para procesamiento bulk de análisis SIASCAFE
"""
import os
import logging
import uuid
from datetime import datetime
from flask import Flask, render_template, request, jsonify, send_file
from flask_cors import CORS
from werkzeug.utils import secure_filename
import threading
from typing import List, Dict
from dotenv import load_dotenv

# Cargar variables de entorno desde .env
load_dotenv()

# Configurar logging primero
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Intentar cargar módulos
try:
    from database import DatabaseManager
    from data_mapper import DataMapper
    from siascafe_client import SIASCAFEClient
    MODULES_LOADED = True
except ImportError as e:
    logger.warning(f"Algunos módulos no se pudieron cargar: {e}")
    MODULES_LOADED = False

# Handler personalizado para capturar logs en el buffer
class WebLogHandler(logging.Handler):
    def emit(self, record):
        try:
            # Filtrar logs que no queremos mostrar en la terminal web
            message = self.format(record)
            
            # Ignorar logs de peticiones GET a /api/logs (evita spam)
            if '/api/logs' in message and 'GET' in message:
                return
            
            # Ignorar logs de health checks frecuentes
            if '/health' in message and 'GET' in message:
                return
            
            # Ignorar logs de polling de estado (/api/status)
            if '/api/status' in message and 'GET' in message:
                return
            
            log_entry = {
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'level': record.levelname,
                'message': message
            }
            logs_buffer.append(log_entry)
            # Mantener solo los últimos MAX_LOGS
            if len(logs_buffer) > MAX_LOGS:
                logs_buffer.pop(0)
        except Exception:
            pass

# Agregar handler personalizado
web_log_handler = WebLogHandler()
web_log_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
logger.addHandler(web_log_handler)

# También agregar a los loggers de otros módulos
logging.getLogger('database').addHandler(web_log_handler)
logging.getLogger('data_mapper').addHandler(web_log_handler)
logging.getLogger('siascafe_client').addHandler(web_log_handler)
logging.getLogger('werkzeug').addHandler(web_log_handler)

app = Flask(__name__, static_url_path='/static')
CORS(app)

# Configurar para que url_for funcione correctamente
app.config['SERVER_NAME'] = None  # Se configurará automáticamente en runtime (puerto 5000)
app.config['APPLICATION_ROOT'] = '/'
app.config['PREFERRED_URL_SCHEME'] = 'http'

# Configuración
UPLOAD_FOLDER = os.path.join(os.getcwd(), 'static', 'pdfs')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Almacenar trabajos en progreso
jobs = {}

# Almacenar logs para mostrar en la terminal web
logs_buffer = []
MAX_LOGS = 1000  # Máximo de líneas de log a mantener


def parse_etapa(raw):
    """Convierte etapa a código numérico"""
    txt = str(raw).strip().upper().replace("Ó", "O")
    mapa = {
        "0": 0,
        "CRECIMIENTO": 0,
        "1": 1,
        "ZOCA": 1,
        "2": 2,
        "PRODUCCION": 2,
        "PRODUCCIÓN": 2,
    }
    return mapa.get(txt, int(raw) if str(raw).isdigit() else 0)


def process_single_analysis(codigo_lab: int, etapa: str, edad: int, densidad: int, sombrio: int, year: int, job_id: str):
    """Procesa un análisis individual"""
    if not MODULES_LOADED:
        jobs[job_id]['results'].append({
            'codigo_lab': codigo_lab,
            'status': 'error',
            'message': 'Módulos no cargados correctamente'
        })
        return
    try:
        # Parsear etapa
        etapa_code = parse_etapa(etapa)
        
        # Conectar a BD
        db = DatabaseManager()
        if not db.connect():
            jobs[job_id]['results'].append({
                'codigo_lab': codigo_lab,
                'status': 'error',
                'message': 'Error al conectar a la base de datos'
            })
            return
        
        try:
            # Buscar muestra
            db_data = db.find_muestra_by_codigo(codigo_lab, year=year)
            if not db_data:
                jobs[job_id]['results'].append({
                    'codigo_lab': codigo_lab,
                    'status': 'error',
                    'message': f'No se encontró muestra con código {codigo_lab}'
                })
                return
            
            # Validar y mapear datos
            user_data = {
                'etapa': etapa_code,
                'edad': edad,
                'densidad': densidad,
                'sombrío': sombrio
            }
            validated_user = DataMapper.validate_user_data(user_data)
            siascafe_data = DataMapper.map_to_siascafe_format(db_data, validated_user)
            
            # Generar PDF con Selenium (headless)
            client = SIASCAFEClient(headless=True, keep_browser_open=False)
            pdf_bytes = client.generate_pdf(siascafe_data, validated_user)
            
            if not pdf_bytes:
                jobs[job_id]['results'].append({
                    'codigo_lab': codigo_lab,
                    'status': 'error',
                    'message': 'No se pudo generar el PDF'
                })
                return
            
            # Guardar PDF
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"resultado_{codigo_lab}_{timestamp}.pdf"
            filepath = os.path.join(UPLOAD_FOLDER, filename)
            
            with open(filepath, 'wb') as f:
                f.write(pdf_bytes)
            
            jobs[job_id]['results'].append({
                'codigo_lab': codigo_lab,
                'status': 'success',
                'filename': filename,
                'message': 'PDF generado correctamente'
            })
            
        finally:
            db.disconnect()
            
    except Exception as e:
        logger.error(f"Error procesando análisis {codigo_lab}: {e}")
        jobs[job_id]['results'].append({
            'codigo_lab': codigo_lab,
            'status': 'error',
            'message': str(e)
        })


def process_bulk_analysis(data: List[Dict], year: int, job_id: str):
    """Procesa múltiples análisis en paralelo"""
    jobs[job_id] = {
        'status': 'processing',
        'total': len(data),
        'completed': 0,
        'results': []
    }
    
    def process_all():
        for row in data:
            process_single_analysis(
                codigo_lab=int(row['codigo_lab']),
                etapa=row['etapa'],
                edad=int(row['edad']),
                densidad=int(row['densidad']),
                sombrio=int(row['sombrio']),
                year=year,
                job_id=job_id
            )
            jobs[job_id]['completed'] += 1
        
        jobs[job_id]['status'] = 'completed'
    
    # Ejecutar en thread separado
    thread = threading.Thread(target=process_all)
    thread.daemon = True
    thread.start()


@app.route('/health')
def health():
    """Endpoint de salud"""
    return jsonify({'status': 'ok', 'message': 'Servidor funcionando'})

@app.route('/')
def index():
    """Página principal"""
    try:
        logger.info("Solicitando página principal")
        return render_template('index.html')
    except Exception as e:
        logger.error(f"Error al renderizar template: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return f"Error al cargar la página: {str(e)}", 500


@app.route('/api/process', methods=['POST'])
def process_analyses():
    """Endpoint para procesar análisis en bulk"""
    try:
        data = request.json
        year = int(data.get('year'))
        analyses = data.get('analyses', [])
        
        if not analyses:
            return jsonify({'error': 'No se proporcionaron análisis'}), 400
        
        # Validar datos
        for analysis in analyses:
            if 'codigo_lab' not in analysis:
                return jsonify({'error': 'Falta código de laboratorio'}), 400
            if 'etapa' not in analysis:
                return jsonify({'error': 'Falta etapa'}), 400
        
        # Crear job ID
        job_id = str(uuid.uuid4())
        
        # Procesar en background
        process_bulk_analysis(analyses, year, job_id)
        
        return jsonify({
            'job_id': job_id,
            'message': f'Procesando {len(analyses)} análisis...'
        })
        
    except Exception as e:
        logger.error(f"Error en /api/process: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/status/<job_id>')
def get_status(job_id):
    """Obtiene el estado de un trabajo"""
    if job_id not in jobs:
        return jsonify({'error': 'Job no encontrado'}), 404
    
    return jsonify(jobs[job_id])


@app.route('/api/download/<filename>')
def download_pdf(filename):
    """Descarga un PDF generado"""
    filepath = os.path.join(UPLOAD_FOLDER, secure_filename(filename))
    if os.path.exists(filepath):
        return send_file(filepath, as_attachment=True)
    return jsonify({'error': 'Archivo no encontrado'}), 404


@app.route('/api/download-all/<job_id>')
def download_all(job_id):
    """Descarga todos los PDFs de un job como ZIP"""
    import zipfile
    import tempfile
    
    if job_id not in jobs:
        return jsonify({'error': 'Job no encontrado'}), 404
    
    # Crear ZIP temporal
    temp_zip = tempfile.NamedTemporaryFile(delete=False, suffix='.zip')
    
    with zipfile.ZipFile(temp_zip.name, 'w') as zipf:
        for result in jobs[job_id]['results']:
            if result['status'] == 'success':
                filepath = os.path.join(UPLOAD_FOLDER, result['filename'])
                if os.path.exists(filepath):
                    zipf.write(filepath, result['filename'])
    
    return send_file(temp_zip.name, as_attachment=True, download_name=f'analisis_{job_id}.zip')


@app.route('/api/logs')
def get_logs():
    """Obtiene los logs para mostrar en la terminal web"""
    # Obtener parámetro 'since' para logs incrementales
    since = request.args.get('since', 0, type=int)
    
    # Retornar logs desde el índice especificado
    if since < len(logs_buffer):
        return jsonify({
            'logs': logs_buffer[since:],
            'total': len(logs_buffer),
            'next_index': len(logs_buffer)
        })
    else:
        return jsonify({
            'logs': [],
            'total': len(logs_buffer),
            'next_index': len(logs_buffer)
        })


@app.route('/api/logs/clear', methods=['POST', 'GET'])
def clear_logs():
    """Limpia el buffer de logs"""
    global logs_buffer
    logs_buffer.clear()
    logger.info("Logs limpiados desde la interfaz web")
    return jsonify({'message': 'Logs limpiados'})


if __name__ == '__main__':
    try:
        # Obtener configuración desde variables de entorno
        host = os.getenv('HOST', '0.0.0.0')
        port = int(os.getenv('PORT', 5000))
        debug = os.getenv('DEBUG', 'False').lower() == 'true'
        
        logger.info("=" * 60)
        logger.info("Iniciando servidor Flask...")
        logger.info(f"Directorio de trabajo: {os.getcwd()}")
        logger.info(f"Templates: {os.path.exists('templates/index.html')}")
        logger.info(f"Static CSS: {os.path.exists('static/css/style.css')}")
        logger.info(f"Static JS: {os.path.exists('static/js/app.js')}")
        logger.info(f"Host: {host}")
        logger.info(f"Puerto: {port}")
        logger.info(f"Debug: {debug}")
        logger.info(f"Servidor disponible en: http://{host}:{port}")
        logger.info("=" * 60)
        app.run(debug=debug, host=host, port=port, use_reloader=False)
    except Exception as e:
        logger.error(f"Error al iniciar servidor: {e}")
        import traceback
        logger.error(traceback.format_exc())

