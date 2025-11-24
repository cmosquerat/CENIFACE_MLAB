"""
Configuración del backend SIASCAFE
"""
import os
import logging
from dotenv import load_dotenv

# Configurar logging primero
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# Cargar variables de entorno desde archivo .env si existe
# Si no existe, las variables pueden venir de docker --env-file o variables de entorno del sistema
env_file_exists = os.path.exists('.env')
load_dotenv()  # Esto carga desde .env si existe, pero no falla si no existe

if env_file_exists:
    logger.info("[CONFIG] Archivo .env encontrado y cargado")
else:
    logger.info("[CONFIG] Archivo .env no encontrado, usando variables de entorno del sistema (--env-file o variables del sistema)")

# Configuración de la base de datos
# Detectar si se usa MySQL o SQLite basado en variables de entorno
DB_HOST = os.getenv('DB_HOST')
DB_PORT = os.getenv('DB_PORT', '3306')
DB_USER = os.getenv('DB_USER')
DB_PASSWORD = os.getenv('DB_PASSWORD')
DB_NAME = os.getenv('DB_NAME')
DB_PATH = os.getenv('DB_PATH', 'multilab.db')

# Determinar tipo de base de datos
USE_MYSQL = bool(DB_HOST and DB_USER and DB_PASSWORD and DB_NAME)
DB_TYPE = "MySQL" if USE_MYSQL else "SQLite"

# Configuración de SIASCAFE (se usa Selenium para automatizar)
SIASCAFE_BASE_URL = os.getenv('SIASCAFE_BASE_URL', 'https://agroclima.cenicafe.org')
SIASCAFE_URL = f"{SIASCAFE_BASE_URL}/siascafe"

# Log detallado de configuración
logger.info("=" * 60)
logger.info("[CONFIG] Configuración de Base de Datos:")
logger.info(f"[CONFIG]   Tipo de BD: {DB_TYPE}")
if USE_MYSQL:
    logger.info(f"[CONFIG]   MySQL Host: {DB_HOST}")
    logger.info(f"[CONFIG]   MySQL Port: {DB_PORT}")
    logger.info(f"[CONFIG]   MySQL User: {DB_USER}")
    logger.info(f"[CONFIG]   MySQL Database: {DB_NAME}")
    logger.info(f"[CONFIG]   MySQL Password: {'*' * len(DB_PASSWORD) if DB_PASSWORD else 'NO CONFIGURADO'}")
else:
    logger.info(f"[CONFIG]   SQLite Path: {DB_PATH}")
logger.info("=" * 60)
logger.info("[CONFIG] Configuración de SIASCAFE:")
logger.info(f"[CONFIG]   SIASCAFE_BASE_URL: {SIASCAFE_BASE_URL}")
logger.info(f"[CONFIG]   SIASCAFE_URL: {SIASCAFE_URL}")
logger.info("=" * 60)

# Configuración del servidor
HOST = os.getenv('HOST', '0.0.0.0')
PORT = int(os.getenv('PORT', 5000))
DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'

# Directorio para guardar PDFs temporalmente
PDF_STORAGE_DIR = os.getenv('PDF_STORAGE_DIR', '/tmp/siascafe_pdfs')

