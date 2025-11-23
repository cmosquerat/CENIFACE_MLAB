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

# Configuración de Proxy (opcional, para evitar bloqueos geográficos)
# Bright Data: http://usuario:contraseña@brd.superproxy.io:33335
# O formato separado:
SIASCAFE_PROXY_HOST = os.getenv('SIASCAFE_PROXY_HOST', '')  # Ej: brd.superproxy.io
SIASCAFE_PROXY_PORT = os.getenv('SIASCAFE_PROXY_PORT', '')  # Ej: 33335
SIASCAFE_PROXY_USER = os.getenv('SIASCAFE_PROXY_USER', '')  # Ej: brd-customer-hl_6ad5dde5-zone-datacenter_proxy1
SIASCAFE_PROXY_PASS = os.getenv('SIASCAFE_PROXY_PASS', '')  # Ej: vekb114yzhdx
# O URL completa (tiene prioridad si está configurada):
SIASCAFE_PROXY_URL = os.getenv('SIASCAFE_PROXY_URL', '')  # Ej: http://user:pass@proxy.com:port

# Construir URL de proxy si se proporcionaron componentes separados
if not SIASCAFE_PROXY_URL and SIASCAFE_PROXY_HOST and SIASCAFE_PROXY_PORT:
    if SIASCAFE_PROXY_USER and SIASCAFE_PROXY_PASS:
        SIASCAFE_PROXY_URL = f"http://{SIASCAFE_PROXY_USER}:{SIASCAFE_PROXY_PASS}@{SIASCAFE_PROXY_HOST}:{SIASCAFE_PROXY_PORT}"
    else:
        SIASCAFE_PROXY_URL = f"http://{SIASCAFE_PROXY_HOST}:{SIASCAFE_PROXY_PORT}"

logger.info("=" * 60)
logger.info("[CONFIG] Configuración cargada:")
logger.info(f"[CONFIG]   DB_PATH: {DB_PATH}")
logger.info(f"[CONFIG]   SIASCAFE_BASE_URL: {SIASCAFE_BASE_URL}")
logger.info(f"[CONFIG]   SIASCAFE_URL: {SIASCAFE_URL}")

# Mostrar configuración de proxy de forma destacada
if SIASCAFE_PROXY_URL:
    # Ocultar contraseña en logs
    proxy_display = SIASCAFE_PROXY_URL
    if '@' in proxy_display:
        parts = proxy_display.split('@')
        if ':' in parts[0]:
            user_pass = parts[0].split(':')
            proxy_display = f"http://{user_pass[0]}:****@{parts[1]}"
    logger.info("=" * 60)
    logger.info("[CONFIG] [PROXY] ✓ PROXY CONFIGURADO")
    logger.info(f"[CONFIG] [PROXY] URL: {proxy_display}")
    logger.info("[CONFIG] [PROXY] Todas las conexiones a SIASCAFE usarán este proxy")
    logger.info("=" * 60)
else:
    logger.warning("=" * 60)
    logger.warning("[CONFIG] [PROXY] ✗ PROXY NO CONFIGURADO")
    logger.warning("[CONFIG] [PROXY] SIASCAFE puede estar bloqueado geográficamente")
    logger.warning("[CONFIG] [PROXY] Configura SIASCAFE_PROXY_URL en .env")
    logger.warning("=" * 60)

# Configuración del servidor
HOST = os.getenv('HOST', '0.0.0.0')
PORT = int(os.getenv('PORT', 5000))
DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'

# Directorio para guardar PDFs temporalmente
PDF_STORAGE_DIR = os.getenv('PDF_STORAGE_DIR', '/tmp/siascafe_pdfs')

