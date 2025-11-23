"""
Configuración del backend SIASCAFE
"""
import os
import logging
from dotenv import load_dotenv

load_dotenv()

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# Configuración de la base de datos SQLite
DB_PATH = os.getenv('DB_PATH', 'multilab.db')

# Configuración de SIASCAFE (se usa Selenium para automatizar)
SIASCAFE_BASE_URL = os.getenv('SIASCAFE_BASE_URL', 'https://agroclima.cenicafe.org')
SIASCAFE_URL = f"{SIASCAFE_BASE_URL}/siascafe"

logger.info("[CONFIG] Configuración cargada:")
logger.info(f"[CONFIG]   DB_PATH: {DB_PATH}")
logger.info(f"[CONFIG]   SIASCAFE_BASE_URL: {SIASCAFE_BASE_URL}")
logger.info(f"[CONFIG]   SIASCAFE_URL: {SIASCAFE_URL}")

# Configuración del servidor
HOST = os.getenv('HOST', '0.0.0.0')
PORT = int(os.getenv('PORT', 5000))
DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'

# Directorio para guardar PDFs temporalmente
PDF_STORAGE_DIR = os.getenv('PDF_STORAGE_DIR', '/tmp/siascafe_pdfs')

