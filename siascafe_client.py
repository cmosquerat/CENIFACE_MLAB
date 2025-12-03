"""
Cliente para interactuar con SIASCAFE usando Selenium
Funciona en modo headless para Linux sin desktop
"""
import logging
import time
import os
from typing import Dict, Optional
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException, WebDriverException
from webdriver_manager.chrome import ChromeDriverManager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

SIASCAFE_URL = 'https://agroclima.cenicafe.org/siascafe'
SELECTORS_FILE = "siascafe_selectors.json"


class SIASCAFEClient:
    """Cliente para comunicarse con SIASCAFE usando Selenium"""
    
    def __init__(self, headless: bool = True, keep_browser_open: bool = False):
        """
        Inicializa el cliente Selenium
        
        Args:
            headless: Si True, ejecuta en modo headless (sin ventana visible)
            keep_browser_open: Si True, no cierra el navegador al finalizar (útil para debug)
        """
        self.headless = headless
        self.keep_browser_open = keep_browser_open
        self.driver = None
        self.selectors = {}
        self._load_selectors()
        self._setup_driver()

    # ------------------------------------------------------------------
    # Manejo de selectores persistentes (XPaths / CSS)
    # ------------------------------------------------------------------
    def _load_selectors(self):
        """Carga selectores guardados de ejecuciones anteriores."""
        try:
            import json
            if os.path.exists(SELECTORS_FILE):
                with open(SELECTORS_FILE, "r", encoding="utf-8") as f:
                    self.selectors = json.load(f)
                logger.info(f"[SELENIUM] Selectores cargados desde {SELECTORS_FILE}")
            else:
                self.selectors = {}
        except Exception as e:
            logger.warning(f"[SELENIUM] No se pudieron cargar selectores: {e}")
            self.selectors = {}

    def _save_selectors(self):
        """Guarda los selectores aprendidos para acelerar futuras ejecuciones."""
        try:
            import json
            with open(SELECTORS_FILE, "w", encoding="utf-8") as f:
                json.dump(self.selectors, f, indent=2, ensure_ascii=False)
            logger.info(f"[SELENIUM] Selectores actualizados guardados en {SELECTORS_FILE}")
        except Exception as e:
            logger.warning(f"[SELENIUM] No se pudieron guardar selectores: {e}")

    def _build_xpath_for_element(self, element) -> str:
        """
        Construye un XPath sencillo y estable para un elemento,
        priorizando atributos id y name.
        """
        try:
            tag = element.tag_name
            elem_id = element.get_attribute("id")
            name = element.get_attribute("name")
            if elem_id:
                return f"//{tag}[@id='{elem_id}']"
            if name:
                return f"//{tag}[@name='{name}']"
        except Exception:
            pass
        # Fallback muy genérico (último recurso)
        return ""

    def _try_saved_locator(self, field_name: str, value: str, search_ctx) -> bool:
        """
        Intenta llenar un campo usando un selector ya guardado (XPath/CSS).
        Devuelve True si lo logró.
        """
        import json  # seguro aquí

        # Para densidad de siembra, fechaMuestreo, edad y sombrio usamos siempre la lógica especial
        # para evitar problemas (concatenación de valores). No usar selectores guardados.
        if field_name == "siembra" or field_name == "fechaMuestreo" or field_name == "edad" or field_name == "sombrio":
            return False

        locators = self.selectors.get(field_name) or []
        for loc in locators:
            by = loc.get("by")
            sel = loc.get("value")
            if not by or not sel:
                continue
            try:
                if by == "xpath":
                    element = search_ctx.find_element(By.XPATH, sel)
                elif by == "css":
                    element = search_ctx.find_element(By.CSS_SELECTOR, sel)
                else:
                    continue
                element.clear()
                element.send_keys(str(value))
                logger.info(f"[SELENIUM] [OK] Campo '{field_name}' llenado con selector guardado ({by}): {sel}")
                return True
            except Exception as e:
                logger.debug(f"[SELENIUM] Selector guardado para '{field_name}' no funcionó ({by}={sel}): {e}")
                continue
        return False

    def _register_locator(self, field_name: str, element):
        """
        Registra un nuevo locator para un campo, basado en id/name del elemento,
        para acelerar futuras ejecuciones.
        """
        xpath = self._build_xpath_for_element(element)
        if not xpath:
            return
        locators = self.selectors.get(field_name) or []
        # Evitar duplicados
        if any(l.get("by") == "xpath" and l.get("value") == xpath for l in locators):
            return
        locators.append({"by": "xpath", "value": xpath})
        self.selectors[field_name] = locators
        logger.info(f"[SELENIUM] Registrado nuevo XPath para '{field_name}': {xpath}")
    
    def _setup_driver(self):
        """Configura el driver de Chrome de manera dinámica (Docker/Linux vs Windows)"""
        try:
            import platform
            current_os = platform.system()
            logger.info(f"[SELENIUM] Detectado sistema operativo: {current_os}")

            logger.info("[SELENIUM] Iniciando configuración de Chrome...")
            chrome_options = Options()
            
            # Directorio de descargas dinámico
            if current_os == 'Windows':
                # En Windows, usar ruta absoluta local
                base_dir = os.getcwd()
                download_dir = os.path.join(base_dir, 'static', 'pdfs')
            else:
                # En Linux/Docker, usar /tmp o lo configurado
                download_dir = os.getenv('PDF_STORAGE_DIR', '/tmp/siascafe_pdfs')
            
            download_dir = os.path.abspath(download_dir)
            os.makedirs(download_dir, exist_ok=True)
            logger.info(f"[SELENIUM] Directorio de descarga configurado: {download_dir}")

            if self.headless:
                logger.info("[SELENIUM] Modo headless activado")
                chrome_options.add_argument('--headless=new')
                chrome_options.add_argument('--no-sandbox')
                chrome_options.add_argument('--disable-dev-shm-usage')
                chrome_options.add_argument('--disable-gpu')
                chrome_options.add_argument('--disable-software-rasterizer')
                
                if current_os == 'Linux':
                    chrome_options.add_argument('--disable-setuid-sandbox')
                
                chrome_options.add_argument('--disable-background-networking')
                chrome_options.add_argument('--disable-background-timer-throttling')
                chrome_options.add_argument('--disable-renderer-backgrounding')
                chrome_options.add_argument('--disable-backgrounding-occluded-windows')
                chrome_options.add_argument('--disable-crash-reporter')
                chrome_options.add_argument('--disable-logging')
                chrome_options.add_argument('--log-level=3')
                
                # Memory tweaks
                chrome_options.add_argument('--max_old_space_size=4096')
                chrome_options.add_argument('--js-flags=--max-old-space-size=4096')
                
                # Optimizaciones específicas para Docker/Contenedores
                # Detectar si estamos en Docker (verificar si existe /.dockerenv)
                is_docker = os.path.exists('/.dockerenv') or os.path.exists('/proc/1/cgroup')
                if is_docker:
                    logger.info("[SELENIUM] Detectado entorno Docker, aplicando optimizaciones...")
                    # Optimizaciones para Docker: reducir uso de memoria y mejorar rendimiento
                    # NOTA: --single-process puede causar problemas de estabilidad, se omite
                    chrome_options.add_argument('--disable-ipc-flooding-protection')
                    chrome_options.add_argument('--disable-features=TranslateUI')
                    chrome_options.add_argument('--disable-features=BlinkGenPropertyTrees')
                    chrome_options.add_argument('--disable-features=IsolateOrigins,site-per-process')
                    chrome_options.add_argument('--disable-site-isolation-trials')
                    chrome_options.add_argument('--disable-features=VizDisplayCompositor')
                    # Reducir timeouts de red y procesos en segundo plano
                    chrome_options.add_argument('--aggressive-cache-discard')
                    chrome_options.add_argument('--disable-hang-monitor')
                    chrome_options.add_argument('--disable-prompt-on-repost')
                    chrome_options.add_argument('--disable-domain-reliability')
                    chrome_options.add_argument('--disable-component-update')
                    chrome_options.add_argument('--disable-client-side-phishing-detection')
                    chrome_options.add_argument('--disable-sync')
                    chrome_options.add_argument('--metrics-recording-only')
                    chrome_options.add_argument('--no-first-run')
                    chrome_options.add_argument('--no-default-browser-check')
                    chrome_options.add_argument('--disable-default-apps')
                    chrome_options.add_argument('--disable-popup-blocking')
                    chrome_options.add_argument('--disable-translate')
                    chrome_options.add_argument('--disable-background-downloads')
                    chrome_options.add_argument('--disable-add-to-shelf')
                    chrome_options.add_argument('--disable-breakpad')
                    chrome_options.add_argument('--disable-component-extensions-with-background-pages')
                    chrome_options.add_argument('--disable-extensions-file-access-check')
                    chrome_options.add_argument('--disable-extensions-http-throttling')
                    chrome_options.add_argument('--disable-renderer-accessibility')
                    chrome_options.add_argument('--force-color-profile=srgb')
                    chrome_options.add_argument('--memory-pressure-off')
                    # Ajustar memoria para Docker (más conservador)
                    chrome_options.add_argument('--max_old_space_size=2048')
                    chrome_options.add_argument('--js-flags=--max-old-space-size=2048')
                    # Mejorar rendimiento de renderizado en Docker
                    chrome_options.add_argument('--disable-accelerated-2d-canvas')
                    chrome_options.add_argument('--disable-accelerated-video-decode')
                    chrome_options.add_argument('--disable-gpu-compositing')
                    logger.info("[SELENIUM] Optimizaciones Docker aplicadas")
            else:
                logger.info("[SELENIUM] Modo con ventana visible")
            
            # Opciones generales
            chrome_options.add_argument('--disable-blink-features=AutomationControlled')
            chrome_options.add_argument('--disable-extensions')
            chrome_options.add_argument('--window-size=1920,1080')
            
            # User Agent
            if current_os == 'Windows':
                 chrome_options.add_argument(
                    '--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                    'AppleWebKit/537.36 (KHTML, like Gecko) '
                    'Chrome/122.0.0.0 Safari/537.36'
                )
            else:
                chrome_options.add_argument(
                    '--user-agent=Mozilla/5.0 (X11; Linux x86_64) '
                    'AppleWebKit/537.36 (KHTML, like Gecko) '
                    'Chrome/122.0.0.0 Safari/537.36'
                )

            prefs = {
                "download.default_directory": download_dir,
                "download.prompt_for_download": False,
                "download.directory_upgrade": True,
                "plugins.always_open_pdf_externally": True
            }
            chrome_options.add_experimental_option("prefs", prefs)
            
            # Configurar ChromeDriver
            logger.info("[SELENIUM] Configurando ChromeDriver...")
            chromedriver_path = None
            
            # 1. Intentar buscar en PATH o ubicaciones comunes
            system_paths = []
            if current_os == 'Windows':
                system_paths = ['chromedriver.exe', 'chromedriver']
            else:
                system_paths = ['/usr/local/bin/chromedriver', '/usr/bin/chromedriver', 'chromedriver']

            import shutil
            for path in system_paths:
                if shutil.which(path) or os.path.exists(path):
                    full_path = shutil.which(path) or os.path.abspath(path)
                    # Verificar si es realmente un ejecutable (en Linux)
                    if current_os == 'Linux' and not os.access(full_path, os.X_OK):
                        continue
                    chromedriver_path = full_path
                    logger.info(f"[SELENIUM] Usando ChromeDriver del sistema: {chromedriver_path}")
                    break
            
            # 2. Si no se encuentra, usar webdriver_manager
            if not chromedriver_path:
                logger.info("[SELENIUM] ChromeDriver local no encontrado, usando webdriver-manager...")
                try:
                    installed_path = ChromeDriverManager().install()
                    logger.info(f"[SELENIUM] webdriver-manager devolvió: {installed_path}")
                    
                    # Lógica robusta para encontrar el ejecutable real
                    # A veces devuelve un archivo .xml, .json o THIRD_PARTY...
                    
                    candidate = installed_path
                    found_executable = False
                    
                    # Si es directorio, buscar dentro
                    if os.path.isdir(candidate):
                        search_dir = candidate
                    else:
                        # Si es archivo, ver si es el ejecutable o algo incorrecto
                        filename = os.path.basename(candidate).lower()
                        is_executable = (
                            (current_os == 'Windows' and filename.endswith('.exe')) or 
                            (current_os != 'Windows' and '.' not in filename)
                        )
                        is_junk = 'third_party' in filename or 'notices' in filename or filename.endswith('.txt')
                        
                        if is_executable and not is_junk:
                            chromedriver_path = candidate
                            found_executable = True
                        else:
                            # Es un archivo incorrecto, buscar en su directorio padre
                            search_dir = os.path.dirname(candidate)
                    
                    if not found_executable:
                        logger.info(f"[SELENIUM] Buscando ejecutable real en: {search_dir}")
                        target_name = 'chromedriver.exe' if current_os == 'Windows' else 'chromedriver'
                        
                        # Búsqueda recursiva
                        for root, dirs, files in os.walk(search_dir):
                            for file in files:
                                if file.lower() == target_name.lower():
                                    full_p = os.path.join(root, file)
                                    # Doble chequeo de "junk"
                                    if 'third_party' in full_p.lower(): 
                                        continue
                                    
                                    chromedriver_path = full_p
                                    found_executable = True
                                    break
                            if found_executable: break
                            
                    if not chromedriver_path:
                        raise Exception(f"No se pudo encontrar {target_name} en {search_dir}")

                    if current_os != 'Windows':
                        os.chmod(chromedriver_path, 0o755)
                        
                    logger.info(f"[SELENIUM] ChromeDriver resuelto: {chromedriver_path}")

                except Exception as e:
                    logger.error(f"[SELENIUM] Error con webdriver-manager: {e}")
                    raise

            # Crear servicio
            service = Service(chromedriver_path)
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            logger.info("[SELENIUM] [OK] Driver inicializado")
            
            # Timeouts - Aumentados para Docker (más lento)
            is_docker = os.path.exists('/.dockerenv') or os.path.exists('/proc/1/cgroup')
            if is_docker:
                logger.info("[SELENIUM] Ajustando timeouts para Docker (más largos)...")
                self.driver.implicitly_wait(20)  # Aumentado de 15 a 20
                self.driver.set_page_load_timeout(180)  # Aumentado de 140 a 180
                self.driver.set_script_timeout(120)  # Aumentado de 80 a 120
            else:
                self.driver.implicitly_wait(15)
                self.driver.set_page_load_timeout(140)
                self.driver.set_script_timeout(80)

        except Exception as e:
            logger.error(f"[SELENIUM] [ERROR] Fallo crítico al inicializar: {e}")
            import traceback
            logger.error(traceback.format_exc())
            raise
    
    def _check_session(self) -> bool:
        """Verifica que la sesión de Chrome esté activa"""
        try:
            if not self.driver:
                logger.warning("[SELENIUM] Driver no inicializado")
                return False
            # Intentar obtener la URL actual (operación simple que verifica la sesión)
            _ = self.driver.current_url
            return True
        except Exception as e:
            error_type = type(e).__name__
            error_msg = str(e)
            # Detectar específicamente el error de sesión perdida
            if "session deleted" in error_msg.lower() or "disconnected" in error_msg.lower():
                logger.error(f"[SELENIUM] Sesión de Chrome cerrada inesperadamente: {error_type}")
            else:
                logger.warning(f"[SELENIUM] Sesión perdida o inválida: {error_type}: {error_msg[:100]}")
            return False
    
    def reset_form(self):
        """Hace clic en el botón 'LIMPIAR DATOS' para reiniciar el formulario"""
        logger.info("[SIASCAFE] Intentando limpiar el formulario (botón 'LIMPIAR DATOS')...")
        try:
            wait = WebDriverWait(self.driver, 10)
            # Buscar botón que contenga "LIMPIAR DATOS"
            reset_btn = wait.until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'LIMPIAR DATOS')]"))
            )
            
            # Asegurar visibilidad
            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center', inline: 'center'});", reset_btn)
            time.sleep(0.5)
            
            # Clic
            self.driver.execute_script("arguments[0].click();", reset_btn)
            logger.info("[SIASCAFE] [OK] Clic en 'LIMPIAR DATOS' realizado")
            
            # Esperar un momento a que se limpie/recargue
            time.sleep(2)
            return True
        except Exception as e:
            logger.warning(f"[SIASCAFE] No se pudo limpiar el formulario: {e}")
            return False

    def generate_pdf(self, form_data: Dict, user_data: Dict, navigate: bool = True) -> Optional[bytes]:
        """
        Genera un PDF usando Selenium para llenar el formulario y descargarlo
        
        Args:
            form_data: Datos del formulario (mapeados desde BD)
            user_data: Datos del usuario (etapa, edad, densidad, sombrío)
            navigate: Si True, navega a la URL. Si False, asume que ya está ahí.
        
        Returns:
            bytes del PDF o None si hay error
        """
        logger.info("[SIASCAFE] ========================================")
        logger.info("[SIASCAFE] Iniciando generación de PDF con Selenium")
        logger.info("[SIASCAFE] ========================================")
        logger.info(f"[SIASCAFE] URL objetivo: {SIASCAFE_URL}")
        logger.info(f"[SIASCAFE] Código muestra: {form_data.get('codigoMuestra', 'N/A')}")
        logger.info(f"[SIASCAFE] Etapa: {user_data.get('etapa', 'N/A')}")
        
        try:
            if navigate:
                # Navegar a SIASCAFE
                logger.info(f"[SELENIUM] Navegando a {SIASCAFE_URL}...")
                start_time = time.time()
                try:
                    # Con pageLoadStrategy=none, no debería bloquearse, pero por si acaso:
                    self.driver.get(SIASCAFE_URL)
                except TimeoutException as e:
                    # Ignorar timeout de carga completa y continuar con lo que ya se haya renderizado
                    logger.warning(f"[SELENIUM] Timeout durante la carga de la página (se continúa de todas formas): {e}")
                load_time = time.time() - start_time
                logger.info(f"[SELENIUM] Llamada a get() completada en {load_time:.2f} segundos")
            else:
                logger.info("[SELENIUM] Saltando navegación (navigate=False)")
            
            # En lugar de esperar un tiempo fijo, esperar explícitamente
            # a que el portlet React principal esté montado.
            logger.info("[SELENIUM] Esperando a que se monte el portlet principal...")
            # Timeout más largo para Docker
            is_docker = os.path.exists('/.dockerenv') or os.path.exists('/proc/1/cgroup')
            portlet_timeout = 80 if is_docker else 50
            logger.info(f"[SELENIUM] Timeout para portlet: {portlet_timeout}s {'(Docker)' if is_docker else '(Local)'}")
            WebDriverWait(self.driver, portlet_timeout).until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, "div[id^='js-portlet-_pacanalisissuelosindividual_INSTANCE_']")
                )
            )
            
            # Verificar título de la página
            try:
                page_title = self.driver.title
                current_url = self.driver.current_url
                logger.info(f"[SELENIUM] Título de la página: {page_title}")
                logger.info(f"[SELENIUM] URL actual: {current_url}")
            except Exception as e:
                logger.warning(f"[SELENIUM] No se pudo obtener título/URL: {e}")
            
            # Verificar si hay errores en la consola
            try:
                logs = self.driver.get_log('browser')
                if logs:
                    logger.warning(f"[SELENIUM] Se encontraron {len(logs)} mensajes en la consola del navegador")
                    for log in logs[:5]:  # Mostrar solo los primeros 5
                        logger.warning(f"[SELENIUM] Console: {log.get('message', '')}")
            except Exception:
                # Algunos drivers o modos no soportan get_log
                pass
            
            logger.info("[SIASCAFE] Llenando formulario...")
            
            # Verificar sesión antes de llenar formulario
            if not self._check_session():
                logger.error("[SELENIUM] La sesión de Chrome se perdió antes de llenar el formulario")
                return None

            # Llenar campos del formulario (incluye espera de 2 segundos después del último dato)
            self._fill_form(form_data, user_data)
            
            # Verificar sesión después de llenar formulario
            if not self._check_session():
                logger.error("[SELENIUM] La sesión de Chrome se perdió después de llenar el formulario")
                return None

            # Enviar formulario
            logger.info("[SIASCAFE] Enviando formulario...")
            self._submit_form()
            
            # Verificar sesión después de enviar formulario
            if not self._check_session():
                logger.error("[SELENIUM] La sesión de Chrome se perdió después de enviar el formulario")
                return None
            
            # Esperar y descargar PDF
            logger.info("[SIASCAFE] Esperando generación de PDF...")
            pdf_content = self._wait_for_pdf()
            
            if pdf_content:
                logger.info(f"[SIASCAFE] [OK] PDF generado exitosamente ({len(pdf_content):,} bytes)")
                return pdf_content
            else:
                logger.error("[SIASCAFE] [ERROR] No se pudo obtener el PDF")
                logger.info("[SIASCAFE] Guardando captura de pantalla para diagnóstico...")
                try:
                    screenshot_path = "/tmp/siascafe_error.png"
                    self.driver.save_screenshot(screenshot_path)
                    logger.info(f"[SIASCAFE] Captura guardada en: {screenshot_path}")
                except Exception:
                    pass
                return None
                
        except Exception as e:
            logger.error(f"[SIASCAFE] [ERROR] Error al generar PDF: {e}")
            import traceback
            logger.error(f"[SIASCAFE] Traceback completo:\n{traceback.format_exc()}")
            return None
    
    def _fill_form(self, form_data: Dict, user_data: Dict):
        """Llena el formulario de SIASCAFE con los datos"""
        logger.info("[SELENIUM] Buscando formulario en la página...")
        # Aumentar timeout porque la app es React/Liferay y tarda en montar
        # Timeout más largo para Docker
        is_docker = os.path.exists('/.dockerenv') or os.path.exists('/proc/1/cgroup')
        form_timeout = 80 if is_docker else 50
        logger.info(f"[SELENIUM] Timeout para formulario: {form_timeout}s {'(Docker)' if is_docker else '(Local)'}")
        wait = WebDriverWait(self.driver, form_timeout)
        container = None
        
        try:
            # 1) Intentar encontrar el contenedor del portlet React por ID conocido
            portlet_selector = "div[id^='js-portlet-_pacanalisissuelosindividual_INSTANCE_']"
            logger.info(f"[SELENIUM] Buscando contenedor del portlet con selector: {portlet_selector}")
            try:
                container = wait.until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, portlet_selector))
                )
                logger.info("[SELENIUM] Contenedor del portlet encontrado")
            except TimeoutException:
                logger.warning("[SELENIUM] No se encontró contenedor específico del portlet, usando toda la página")
            
            # Guardar HTML de la página para diagnóstico
            try:
                html_dump_path = os.path.abspath("siascafe_dom_after_load.html")
                with open(html_dump_path, "w", encoding="utf-8") as f:
                    f.write(self.driver.page_source)
                logger.info(f"[SELENIUM] HTML completo de la página guardado en: {html_dump_path}")
            except Exception as e:
                logger.warning(f"[SELENIUM] No se pudo guardar HTML de la página: {e}")
            
            # 2) Si tenemos contenedor, intentar esperar a que se monten inputs dentro de él
            search_context = container if container is not None else self.driver
            inputs = []
            if container is not None:
                try:
                    container_id = container.get_attribute("id")
                    logger.info(f"[SELENIUM] ID del contenedor del portlet: {container_id}")
                    container_input_selector = f"#{container_id} input, #{container_id} textarea, #{container_id} select"
                    logger.info(f"[SELENIUM] Esperando inputs dentro del contenedor con selector: {container_input_selector}")
                    wait.until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, container_input_selector))
                    )
                    inputs = self.driver.find_elements(By.CSS_SELECTOR, container_input_selector)
                    logger.info(f"[SELENIUM] Se encontraron {len(inputs)} campos de entrada dentro del contenedor")
                except TimeoutException:
                    logger.warning("[SELENIUM] Timeout esperando inputs dentro del contenedor del portlet")
                except Exception as e:
                    logger.warning(f"[SELENIUM] Error buscando inputs dentro del contenedor: {e}")
            
            # 3) Si no se encontraron inputs en el contenedor, buscar en toda la página
            if not inputs:
                logger.warning("[SELENIUM] No se encontraron campos en el contenedor, buscando en toda la página...")
                inputs = self.driver.find_elements(By.CSS_SELECTOR, "input, textarea, select")
                logger.info(f"[SELENIUM] Campos encontrados en toda la página: {len(inputs)}")
            
            if not inputs:
                logger.error("[SELENIUM] No se encontraron campos de formulario en la página")
                raise TimeoutException("No se encontraron campos input/textarea/select")
            
            time.sleep(2)
            
            # Normalizar densidad de siembra como en el script original:
            #   - Valores permitidos: 2000, 2200, ..., 22000 (pasos de 200)
            #   - Se elige el valor más cercano al ingresado por el usuario
            try:
                densidad_usuario = int(user_data.get('densidad', 2000))
                posibles = list(range(2000, 22001, 200))
                densidad_normalizada = min(posibles, key=lambda x: abs(x - densidad_usuario))
                logger.info(
                    f"[SELENIUM] Densidad de siembra. Usuario={densidad_usuario} -> Normalizada={densidad_normalizada}"
                )
            except Exception as e:
                logger.warning(f"[SELENIUM] No se pudo normalizar densidad, se usa valor crudo: {e}")
                densidad_normalizada = user_data.get('densidad', 2000)

            # Mapear y llenar campos (incluyendo siembra como input number)
            field_mapping = {
                'nombre': form_data.get('nombre', ''),
                'departamento': form_data.get('departamento', ''),
                'municipio': form_data.get('municipio', ''),
                'codigoMuestra': form_data.get('codigoMuestra', ''),
                'codigo': form_data.get('codigo', ''),
                'finca': form_data.get('finca', ''),
                'lote': form_data.get('lote', ''),
                'edad': str(user_data.get('edad', 0)),
                'siembra': str(densidad_normalizada),
                'sombrio': str(user_data.get('sombrío', 0)),
                'fechaMuestreo': form_data.get('fechaMuestreo', ''),
                'pH': str(form_data.get('pH', '') or ''),
                'MO': str(form_data.get('MO', '') or ''),
                'P': str(form_data.get('P', '') or ''),
                'K': str(form_data.get('K', '') or ''),
                'Mg': str(form_data.get('Mg', '') or ''),
                'Ca': str(form_data.get('Ca', '') or ''),
                'Al': str(form_data.get('Al', '') or ''),
                'S': str(form_data.get('S', '') or ''),
            }
            
            # Llenar campos de texto (inputs/textarea) usando los name/id exactos del formulario
            filled_count = 0
            search_ctx = container if container is not None else self.driver
            for field_name, value in field_mapping.items():
                if not value:
                    continue
                try:
                    logger.info(f"[SELENIUM] Intentando llenar campo '{field_name}' con valor '{value}'")

                    # 1) Intentar con selector guardado (XPath/CSS)
                    if self._try_saved_locator(field_name, value, search_ctx):
                        filled_count += 1
                        continue

                    # 2) Heurística por name/id/placeholder
                    selectors = [
                        f"input[name='{field_name}']",
                        f"input[id='{field_name}']",
                        f"textarea[name='{field_name}']",
                        f"textarea[id='{field_name}']",
                        f"input[placeholder*='{field_name}']",
                        f"input[placeholder*='{field_name.upper()}']",
                    ]
                    
                    filled = False
                    for selector in selectors:
                        try:
                            # Campo especial: siembra (densidad de siembra)
                            if field_name == "siembra":
                                # Usar siempre el input exacto con id=":r9:" y simular edición de texto
                                element = self.driver.find_element(By.ID, ":r9:")
                                element.click()
                                element.send_keys(Keys.CONTROL, "a")
                                element.send_keys(Keys.BACKSPACE)
                                element.send_keys(str(value))
                                logger.info(f"[SELENIUM] [OK] Campo 'siembra' (id=':r9:') establecido a: {value}")
                            # Campo especial: edad (limpiar antes de escribir para evitar concatenación)
                            elif field_name == "edad":
                                # Usar siempre el input exacto con id=":r8:" y limpiar antes de escribir
                                element = self.driver.find_element(By.ID, ":r8:")
                                element.click()
                                element.send_keys(Keys.CONTROL, "a")
                                element.send_keys(Keys.BACKSPACE)
                                element.send_keys(str(value))
                                logger.info(f"[SELENIUM] [OK] Campo 'edad' (id=':r8:') establecido a: {value}")
                            # Campo especial: sombrio (limpiar antes de escribir para evitar concatenación)
                            elif field_name == "sombrio":
                                # Usar siempre el input exacto con id=":ra:" y limpiar antes de escribir
                                element = self.driver.find_element(By.ID, ":ra:")
                                element.click()
                                element.send_keys(Keys.CONTROL, "a")
                                element.send_keys(Keys.BACKSPACE)
                                element.send_keys(str(value))
                                logger.info(f"[SELENIUM] [OK] Campo 'sombrio' (id=':ra:') establecido a: {value}")
                            # Campo especial: fecha de muestreo (convertir de YYYY-MM-DD a DD/MM/YYYY)
                            elif field_name == "fechaMuestreo":
                                # Usar siempre el input exacto con id=":rb:"
                                element = self.driver.find_element(By.ID, ":rb:")
                                
                                # DIAGNÓSTICO: Verificar tipo y atributos del campo
                                campo_type = element.get_attribute("type")
                                campo_name = element.get_attribute("name")
                                valor_antes = element.get_attribute("value")
                                logger.info(f"[SELENIUM] [DIAGNÓSTICO] Campo fechaMuestreo:")
                                logger.info(f"[SELENIUM]   - type: {campo_type}")
                                logger.info(f"[SELENIUM]   - name: {campo_name}")
                                logger.info(f"[SELENIUM]   - valor antes: '{valor_antes}'")
                                
                                raw = str(value or "").strip()
                                logger.info(f"[SELENIUM] [DIAGNÓSTICO] Valor recibido desde form_data: '{raw}' (tipo: {type(value)})")
                                
                                # Convertir de YYYY-MM-DD a DD/MM/YYYY
                                fecha_formateada = ""
                                fecha_iso = ""
                                if raw:
                                    # Extraer solo la parte de fecha (antes de cualquier espacio)
                                    token = raw.split()[0] if raw else ""
                                    token = token[:10]  # Máximo 10 caracteres para YYYY-MM-DD
                                    logger.info(f"[SELENIUM] [DIAGNÓSTICO] Token extraído: '{token}'")
                                    
                                    # Parsear formato YYYY-MM-DD
                                    if len(token) == 10 and token[4] == "-" and token[7] == "-":
                                        try:
                                            yyyy_str, mm_str, dd_str = token.split("-")
                                            yyyy = int(yyyy_str)
                                            mm = int(mm_str)
                                            dd = int(dd_str)
                                            logger.info(f"[SELENIUM] [DIAGNÓSTICO] Componentes parseados: año={yyyy}, mes={mm}, día={dd}")
                                            
                                            # Validar y convertir a DD/MM/YYYY
                                            if 1900 <= yyyy <= 2100 and 1 <= mm <= 12 and 1 <= dd <= 31:
                                                fecha_formateada = f"{dd:02d}/{mm:02d}/{yyyy:04d}"
                                                fecha_iso = f"{yyyy:04d}-{mm:02d}-{dd:02d}"
                                                logger.info(f"[SELENIUM] [DIAGNÓSTICO] Fecha convertida: {token} -> DD/MM/YYYY={fecha_formateada}, ISO={fecha_iso}")
                                            else:
                                                logger.warning(f"[SELENIUM] Fecha fuera de rango válido: {token}")
                                        except ValueError as e:
                                            logger.warning(f"[SELENIUM] Error al parsear fecha '{token}': {e}")
                                    else:
                                        logger.warning(f"[SELENIUM] Token '{token}' no tiene formato YYYY-MM-DD")
                                
                                # Si no se pudo convertir, usar fecha actual
                                if not fecha_formateada:
                                    from datetime import date as _date
                                    today = _date.today()
                                    fecha_formateada = today.strftime("%d/%m/%Y")
                                    fecha_iso = today.strftime("%Y-%m-%d")
                                    logger.warning(
                                        f"[SELENIUM] Fecha de muestreo inválida '{raw}', usando fecha actual DD/MM/YYYY={fecha_formateada}, ISO={fecha_iso}"
                                    )
                                
                                # SIEMPRE usar formato DD/MM/YYYY como indicó el usuario
                                logger.info(f"[SELENIUM] Usando formato DD/MM/YYYY: {fecha_formateada}")
                                
                                # Hacer clic en el campo para enfocarlo
                                element.click()
                                time.sleep(0.1)
                                
                                # Limpiar el campo completamente usando teclado
                                element.send_keys(Keys.CONTROL, "a")
                                time.sleep(0.1)
                                element.send_keys(Keys.BACKSPACE)
                                time.sleep(0.1)
                                
                                # Escribir la fecha en formato DD/MM/YYYY carácter por carácter
                                # para asegurar que se ingrese correctamente
                                element.send_keys(fecha_formateada)
                                time.sleep(0.2)
                                
                                # Verificar valor después de escribir
                                valor_despues = element.get_attribute("value")
                                logger.info(f"[SELENIUM] [DIAGNÓSTICO] Valor después de escribir (value attribute): '{valor_despues}'")
                                
                                # También verificar el valor visible en el campo
                                try:
                                    valor_visible = element.get_property("value") or element.get_attribute("value")
                                    logger.info(f"[SELENIUM] [DIAGNÓSTICO] Valor visible en campo (property): '{valor_visible}'")
                                except:
                                    pass
                                
                                # Verificar que el valor se escribió correctamente
                                if fecha_formateada in str(valor_despues) or fecha_formateada in str(valor_visible):
                                    logger.info(f"[SELENIUM] [OK] Campo 'fechaMuestreo' establecido correctamente a: {fecha_formateada}")
                                else:
                                    logger.warning(f"[SELENIUM] [ADVERTENCIA] Campo 'fechaMuestreo' puede no haberse establecido correctamente. Esperado: {fecha_formateada}, Obtenido: {valor_despues}")
                                
                                filled = True
                                filled_count += 1
                                break
                            else:
                                element = search_ctx.find_element(By.CSS_SELECTOR, selector)
                                element.clear()
                                element.send_keys(str(value))
                                logger.info(f"[SELENIUM] [OK] Campo '{field_name}' llenado: {value} (selector: {selector})")
                                # Registrar XPath para próximas ejecuciones (no registrar para campos especiales)
                                if field_name not in ("siembra", "fechaMuestreo", "edad", "sombrio"):
                                    self._register_locator(field_name, element)
                                filled = True
                                filled_count += 1
                                break
                        except Exception as e:
                            logger.debug(f"[SELENIUM] Selector '{selector}' no funcionó: {e}")
                            continue
                    
                    if not filled:
                        logger.warning(f"[SELENIUM] Campo '{field_name}' no encontrado con ningún selector")
                except Exception as e:
                    logger.warning(f"[SELENIUM] Error al llenar '{field_name}': {e}")
                # Pequeña pausa entre campos para dar tiempo al frontend a reaccionar
                time.sleep(0.1)
            
            logger.info(f"[SELENIUM] Total de campos llenados: {filled_count}/{len([v for v in field_mapping.values() if v])}")
            
            # Seleccionar etapa: interactuar con el componente MUI Select
            etapa = user_data.get('etapa', 0)
            logger.info(f"[SELENIUM] Seleccionando etapa (valor lógico): {etapa}")
            
            # Mapeo de valores numéricos a texto visible en el select
            etapa_textos = {
                0: "Crecimiento",
                1: "Zoca",
                2: "Producción"
            }
            etapa_texto = etapa_textos.get(etapa, "Crecimiento")
            
            try:
                # 1. Encontrar el elemento MUI Select por su ID
                select_element = wait.until(
                    EC.element_to_be_clickable((By.ID, "mui-component-select-etapa"))
                )
                logger.info(f"[SELENIUM] Select de etapa encontrado, haciendo clic para abrir menú...")
                
                # 2. Hacer clic para abrir el menú desplegable
                select_element.click()
                time.sleep(0.5)  # Pequeña pausa para que se abra el menú
                
                # 3. Esperar a que aparezca el menú (usando aria-controls)
                menu_id = select_element.get_attribute("aria-controls")
                if menu_id:
                    logger.info(f"[SELENIUM] Esperando menú desplegable con ID: {menu_id}")
                    menu = wait.until(
                        EC.presence_of_element_located((By.ID, menu_id))
                    )
                    
                    # 4. Buscar la opción por texto o por data-value
                    # Intentar primero por data-value (más confiable)
                    try:
                        option = menu.find_element(By.XPATH, f".//li[@data-value='{etapa}']")
                        logger.info(f"[SELENIUM] Opción encontrada por data-value={etapa}")
                    except:
                        # Fallback: buscar por texto visible
                        logger.info(f"[SELENIUM] Buscando opción por texto: '{etapa_texto}'")
                        option = menu.find_element(By.XPATH, f".//li[contains(text(), '{etapa_texto}')]")
                    
                    # 5. Hacer clic en la opción
                    option.click()
                    time.sleep(0.3)
                    logger.info(f"[SELENIUM] [OK] Etapa '{etapa_texto}' (valor {etapa}) seleccionada correctamente")
                    
                    # 6. Verificar que el input oculto también se actualizó
                    try:
                        hidden_input = self.driver.find_element(By.NAME, "etapa")
                        hidden_value = hidden_input.get_attribute("value")
                        if hidden_value == str(etapa):
                            logger.info(f"[SELENIUM] [OK] Input oculto 'etapa' también actualizado a {etapa}")
                        else:
                            logger.warning(f"[SELENIUM] Input oculto tiene valor {hidden_value}, esperado {etapa}")
                            # Forzar actualización del input oculto como respaldo
                            self.driver.execute_script(
                                "var el = document.querySelector(\"input[name='etapa']\");"
                                "if (el) { el.value = arguments[0]; }",
                                str(etapa),
                            )
                    except Exception as e2:
                        logger.warning(f"[SELENIUM] No se pudo verificar/actualizar input oculto: {e2}")
                else:
                    logger.warning("[SELENIUM] No se encontró aria-controls en el select, intentando método alternativo...")
                    # Método alternativo: buscar opciones directamente
                    options = self.driver.find_elements(By.XPATH, "//ul[@role='listbox']//li")
                    for opt in options:
                        if str(etapa) in opt.get_attribute("data-value") or etapa_texto in opt.text:
                            opt.click()
                            time.sleep(0.3)
                            logger.info(f"[SELENIUM] [OK] Etapa seleccionada usando método alternativo")
                            break
                    
            except Exception as e:
                logger.error(f"[SELENIUM] [ERROR] Error al seleccionar etapa: {e}")
                import traceback
                logger.error(traceback.format_exc())
                # Fallback: intentar establecer el input oculto directamente
                try:
                    self.driver.execute_script(
                        "var el = document.querySelector(\"input[name='etapa']\");"
                        "if (el) { el.value = arguments[0]; }",
                        str(etapa),
                    )
                    logger.warning(f"[SELENIUM] Usando fallback: input oculto establecido a {etapa}")
                except:
                    logger.error("[SELENIUM] Fallback también falló")

            # Densidad ya se llenó como input[name='siembra']; no hay select separado

            # Seleccionar textura: interactuar con el componente MUI Select (igual que etapa)
            logger.info("[SELENIUM] Seleccionando textura...")
            
            textura_val = form_data.get('Textura', "0")
            textura_str = str(textura_val) if textura_val else "0"
            logger.info(f"[SELENIUM] Valor de textura desde form_data: {textura_str}")
            
            try:
                # 1. Encontrar el elemento MUI Select por su ID (igual que etapa)
                select_element = wait.until(
                    EC.presence_of_element_located((By.ID, "mui-component-select-Textura"))
                )
                logger.info(f"[SELENIUM] Select de textura encontrado, haciendo scroll y clic para abrir menú...")
                
                # Hacer scroll al elemento para asegurar que esté visible y clickeable
                self.driver.execute_script(
                    "arguments[0].scrollIntoView({block: 'center', inline: 'center'});",
                    select_element
                )
                time.sleep(0.3)  # Pequeña pausa después del scroll
                
                # 2. Hacer clic para abrir el menú desplegable (igual que etapa)
                select_element.click()
                time.sleep(0.5)  # Pequeña pausa para que se abra el menú
                
                # 3. Esperar a que aparezca el menú (usando aria-controls, igual que etapa)
                menu_id = select_element.get_attribute("aria-controls")
                if menu_id:
                    logger.info(f"[SELENIUM] Esperando menú de textura con ID: {menu_id}")
                    menu = wait.until(
                        EC.presence_of_element_located((By.ID, menu_id))
                    )
                    
                    # 4. Buscar la opción por data-value (igual que etapa)
                    try:
                        option = menu.find_element(By.XPATH, f".//li[@data-value='{textura_str}']")
                        logger.info(f"[SELENIUM] Opción de textura encontrada por data-value={textura_str}")
                    except:
                        logger.warning(f"[SELENIUM] No se encontró opción por data-value='{textura_str}', intentando método alternativo...")
                        # Fallback: buscar opciones directamente
                        options = self.driver.find_elements(By.XPATH, "//ul[@role='listbox']//li")
                        option = None
                        for opt in options:
                            if textura_str == opt.get_attribute("data-value"):
                                option = opt
                                break
                        if not option:
                            raise Exception(f"No se encontró opción con data-value='{textura_str}'")
                    
                    # 5. Hacer clic en la opción (igual que etapa)
                    option.click()
                    time.sleep(0.3)
                    logger.info(f"[SELENIUM] [OK] Textura '{textura_str}' seleccionada correctamente")
                    
                    # 6. Verificar que el input oculto también se actualizó (igual que etapa)
                    try:
                        hidden_input = self.driver.find_element(By.NAME, "Textura")
                        hidden_value = hidden_input.get_attribute("value")
                        if hidden_value == textura_str:
                            logger.info(f"[SELENIUM] [OK] Input oculto 'Textura' también actualizado a {textura_str}")
                        else:
                            logger.warning(f"[SELENIUM] Input oculto tiene valor {hidden_value}, esperado {textura_str}")
                            # Forzar actualización del input oculto como respaldo
                            self.driver.execute_script(
                                "var el = document.querySelector(\"input[name='Textura']\");"
                                "if (el) { el.value = arguments[0]; }",
                                textura_str,
                            )
                    except Exception as e2:
                        logger.warning(f"[SELENIUM] No se pudo verificar/actualizar input oculto: {e2}")
                else:
                    logger.warning("[SELENIUM] No se encontró aria-controls en el select de textura, intentando método alternativo...")
                    # Método alternativo: buscar opciones directamente (igual que etapa)
                    options = self.driver.find_elements(By.XPATH, "//ul[@role='listbox']//li")
                    for opt in options:
                        if textura_str == opt.get_attribute("data-value"):
                            opt.click()
                            time.sleep(0.3)
                            logger.info(f"[SELENIUM] [OK] Textura seleccionada usando método alternativo")
                            break
                        
            except Exception as e:
                logger.error(f"[SELENIUM] [ERROR] Error al seleccionar textura: {e}")
                import traceback
                logger.error(traceback.format_exc())
                # Fallback: intentar establecer el input oculto directamente (igual que etapa)
                try:
                    self.driver.execute_script(
                        "var el = document.querySelector(\"input[name='Textura']\");"
                        "if (el) { el.value = arguments[0]; }",
                        textura_str,
                    )
                    logger.warning(f"[SELENIUM] Usando fallback: input oculto establecido a {textura_str}")
                except:
                    logger.error("[SELENIUM] Fallback también falló")
            
            # QUITAR EL FOCO del último campo para que se registre el valor
            logger.info("[SELENIUM] Quitando el foco del último campo para que se registre el valor...")
            try:
                # Presionar Tab para mover el foco fuera del campo actual
                active_element = self.driver.switch_to.active_element
                active_element.send_keys(Keys.TAB)
                time.sleep(0.2)
                logger.info("[SELENIUM] [OK] Foco movido fuera del campo usando Tab")
            except Exception as e:
                # Fallback: hacer clic en el body de la página
                try:
                    body = self.driver.find_element(By.TAG_NAME, "body")
                    body.click()
                    time.sleep(0.2)
                    logger.info("[SELENIUM] [OK] Foco movido fuera del campo haciendo clic en body")
                except Exception as e2:
                    logger.warning(f"[SELENIUM] No se pudo quitar el foco del campo: {e2}")
            
            # Guardar selectores aprendidos en disco para acelerar futuros runs
            self._save_selectors()
            logger.info("[SELENIUM] [OK] Formulario llenado completamente")
            
        except TimeoutException:
            logger.error("[SIASCAFE] Timeout esperando formulario")
            raise
        except Exception as e:
            logger.error(f"[SIASCAFE] Error al llenar formulario: {e}")
            raise
    
    def _submit_form(self):
        """Envía el formulario"""
        logger.info("[SELENIUM] Enviando formulario con botón 'Enviar Datos'...")
        try:
            # Tu botón concreto: <button type="submit">Enviar Datos</button>
            try:
                # Localizar directamente por XPath usando el texto visible "Enviar Datos"
                submit_btn = self.driver.find_element(
                    By.XPATH, "//button[@type='submit' and normalize-space(.)='Enviar Datos']"
                )
                logger.info("[SELENIUM] Botón de envío localizado por XPath con texto 'Enviar Datos'")
                # Asegurarnos de que es clickeable: scroll al centro y click por JS
                self.driver.execute_script(
                    "arguments[0].scrollIntoView({block: 'center', inline: 'center'});",
                    submit_btn,
                )
                self.driver.execute_script("arguments[0].click();", submit_btn)
                logger.info("[SELENIUM] [OK] Formulario enviado haciendo clic JS en botón 'Enviar Datos'")
                time.sleep(2)
            except Exception as e:
                logger.error(f"[SELENIUM] No se pudo hacer clic en botón 'Enviar Datos': {e}")
                logger.info("[SELENIUM] Intentando enviar formulario con form.submit()...")
                try:
                    form = self.driver.find_element(By.CSS_SELECTOR, "form")
                    form.submit()
                    logger.info("[SELENIUM] [OK] Formulario enviado con form.submit()")
                    time.sleep(2)
                except Exception as e2:
                    logger.error(f"[SELENIUM] No se pudo enviar el formulario ni con form.submit(): {e2}")
            
        except Exception as e:
            logger.error(f"[SELENIUM] [ERROR] Error al enviar formulario: {e}")
            import traceback
            logger.error(traceback.format_exc())
            raise
    
    def _wait_for_pdf(self, timeout: int = None) -> Optional[bytes]:
        """Espera a que aparezca el botón 'Descargar PDF', hace clic y descarga el PDF"""
        try:
            import platform
            current_os = platform.system()
            
            # Determinar directorio de descargas según SO
            if current_os == 'Windows':
                base_dir = os.getcwd()
                download_dir = os.path.join(base_dir, 'static', 'pdfs')
            else:
                download_dir = os.getenv('PDF_STORAGE_DIR', '/tmp/siascafe_pdfs')
            
            download_dir = os.path.abspath(download_dir)
            logger.info(f"[SIASCAFE] Buscando PDF en: {download_dir}")

            # Timeout dinámico según entorno (reducido para evitar esperas innecesarias)
            is_docker = os.path.exists('/.dockerenv') or os.path.exists('/proc/1/cgroup')
            if timeout is None:
                # Timeout más corto para buscar el botón (30s debería ser suficiente)
                button_search_timeout = 30 if is_docker else 20
                # Timeout más largo solo para la descarga del archivo PDF
                download_timeout = 60 if is_docker else 40
            else:
                button_search_timeout = min(timeout // 2, 30)  # Máximo 30s para buscar botón
                download_timeout = timeout
            
            logger.info(f"[SIASCAFE] Timeout para buscar botón: {button_search_timeout}s, Timeout para descarga: {download_timeout}s {'(Docker)' if is_docker else '(Local)'}")

            logger.info("[SIASCAFE] Esperando a que aparezca el botón 'Descargar PDF'...")
            
            # Estrategia 1: Buscar primero por presencia (más rápido), luego verificar si es clickeable
            download_button = None
            wait_presence = WebDriverWait(self.driver, button_search_timeout)
            wait_clickable = WebDriverWait(self.driver, 5)  # Timeout corto para verificar clickeable
            
            try:
                # Primero buscar por presencia (más rápido que clickeable)
                logger.info("[SIASCAFE] Buscando botón por presencia...")
                download_button = wait_presence.until(
                    EC.presence_of_element_located(
                        (By.XPATH, "//span[@role='button' and contains(., 'Descargar PDF')]")
                    )
                )
                logger.info("[SIASCAFE] [OK] Botón encontrado por presencia, verificando si es clickeable...")
                
                # Verificar si es clickeable (con timeout corto)
                try:
                    download_button = wait_clickable.until(
                        EC.element_to_be_clickable(
                            (By.XPATH, "//span[@role='button' and contains(., 'Descargar PDF')]")
                        )
                    )
                    logger.info("[SIASCAFE] [OK] Botón es clickeable")
                except TimeoutException:
                    logger.warning("[SIASCAFE] Botón encontrado pero no es clickeable aún, intentando de todas formas...")
                    # Intentar de todas formas, puede que funcione
                    
            except TimeoutException:
                # Estrategia 2: Buscar por ícono como fallback
                logger.info("[SIASCAFE] No se encontró por texto, buscando por ícono AssignmentReturnedIcon...")
                try:
                    wait_icon = WebDriverWait(self.driver, button_search_timeout)
                    icon = wait_icon.until(
                        EC.presence_of_element_located(
                            (By.CSS_SELECTOR, "svg[data-testid='AssignmentReturnedIcon']")
                        )
                    )
                    # Encontrar el span padre con role="button" que contiene el ícono
                    download_button = icon.find_element(By.XPATH, "./ancestor::span[@role='button']")
                    logger.info("[SIASCAFE] [OK] Botón 'Descargar PDF' encontrado por ícono")
                except Exception as e:
                    logger.error(f"[SIASCAFE] [ERROR] No se pudo encontrar el botón 'Descargar PDF' después de {button_search_timeout}s: {e}")
                    # Guardar HTML para diagnóstico
                    try:
                        html_path = '/tmp/siascafe_page_before_download.html'
                        with open(html_path, 'w', encoding='utf-8') as f:
                            f.write(self.driver.page_source)
                        logger.info(f"[SIASCAFE] HTML guardado en {html_path} para diagnóstico")
                    except:
                        pass
                    return None
            
            if not download_button:
                logger.error("[SIASCAFE] [ERROR] No se pudo obtener referencia al botón")
                return None
            
            # Hacer clic en el botón "Descargar PDF"
            logger.info("[SIASCAFE] Haciendo clic en el botón 'Descargar PDF'...")
            try:
                # Scroll al botón y hacer clic con JavaScript para evitar intercepciones
                self.driver.execute_script("arguments[0].scrollIntoView({block: 'center', inline: 'center'});", download_button)
                time.sleep(0.5)
                self.driver.execute_script("arguments[0].click();", download_button)
                logger.info("[SIASCAFE] [OK] Clic en botón 'Descargar PDF' realizado")
            except Exception as e:
                logger.warning(f"[SIASCAFE] Error al hacer clic con JS, intentando clic normal: {e}")
                download_button.click()
            
            # Esperar a que el PDF se descargue en el directorio de descargas
            # download_dir ya se definió arriba
            os.makedirs(download_dir, exist_ok=True)
            
            logger.info(f"[SIASCAFE] Esperando descarga del PDF en {download_dir} (hasta {download_timeout} segundos)...")
            start_time = time.time()
            check_interval = 1  # Verificar cada segundo
            initial_files = set()
            if os.path.exists(download_dir):
                initial_files = set([f for f in os.listdir(download_dir) if f.endswith('.pdf')])
            
            while time.time() - start_time < download_timeout:
                if os.path.exists(download_dir):
                    current_files = set([f for f in os.listdir(download_dir) if f.endswith('.pdf')])
                    new_files = current_files - initial_files
                    
                    if new_files:
                        # Hay archivos nuevos, esperar a que termine de descargarse
                        for filename in new_files:
                            file_path = os.path.join(download_dir, filename)
                            try:
                                # Verificar que el archivo no esté siendo escrito (tamaño estable)
                                file_size = os.path.getsize(file_path)
                                time.sleep(1)  # Esperar 1 segundo
                                new_size = os.path.getsize(file_path)
                                
                                if file_size > 0 and file_size == new_size:
                                    logger.info(f"[SIASCAFE] PDF descargado: {file_path} (tamaño: {file_size:,} bytes)")
                                    with open(file_path, 'rb') as f:
                                        content = f.read()
                                    logger.info(f"[SIASCAFE] [OK] PDF leído exitosamente ({len(content):,} bytes)")
                                    # Limpiar el archivo temporal
                                    try:
                                        os.remove(file_path)
                                        logger.info(f"[SIASCAFE] Archivo temporal {file_path} eliminado")
                                    except:
                                        pass
                                    return content
                                else:
                                    logger.debug(f"[SIASCAFE] PDF aún descargándose: {filename} (tamaño cambiando: {file_size} -> {new_size} bytes)")
                            except Exception as e:
                                logger.debug(f"[SIASCAFE] Error verificando archivo {filename}: {e}")
                
                elapsed = time.time() - start_time
                if elapsed < download_timeout:
                    time.sleep(check_interval)
                    if int(elapsed) % 5 == 0:  # Log cada 5 segundos
                        logger.info(f"[SIASCAFE] Esperando descarga del PDF... ({int(elapsed)}/{download_timeout} segundos)")
            
            logger.error(f"[SIASCAFE] Timeout de {download_timeout} segundos alcanzado esperando descarga del PDF")
            
            # Guardar HTML para diagnóstico
            logger.info("[SIASCAFE] Guardando página HTML para análisis...")
            try:
                with open('/tmp/siascafe_page.html', 'w', encoding='utf-8') as f:
                    f.write(self.driver.page_source)
                logger.info("[SIASCAFE] HTML guardado en /tmp/siascafe_page.html")
            except:
                pass
            
            return None
            
        except Exception as e:
            logger.error(f"[SIASCAFE] Error al obtener PDF: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return None
    
    def __del__(self):
        """Cierra el driver al destruir el objeto (a menos que keep_browser_open=True)"""
        if self.driver and not self.keep_browser_open:
            try:
                self.driver.quit()
            except:
                pass
        elif self.driver and self.keep_browser_open:
            logger.info("[SELENIUM] Navegador mantenido abierto para debug (keep_browser_open=True)")
