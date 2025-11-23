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
        """Configura el driver de Chrome para Linux headless"""
        try:
            logger.info("[SELENIUM] Iniciando configuración de Chrome...")
            chrome_options = Options()
            
            if self.headless:
                logger.info("[SELENIUM] Modo headless activado")
                chrome_options.add_argument('--headless=new')
                chrome_options.add_argument('--no-sandbox')
                chrome_options.add_argument('--disable-dev-shm-usage')
                chrome_options.add_argument('--disable-gpu')
                # Opciones adicionales para servidores sin entorno gráfico
                chrome_options.add_argument('--disable-software-rasterizer')
                # --single-process puede causar problemas en Windows, solo usarlo en Linux
                import platform
                if platform.system() == 'Linux':
                    chrome_options.add_argument('--disable-setuid-sandbox')
                    # NO usar --single-process ya que puede causar que Chrome se cierre inesperadamente
                    # chrome_options.add_argument('--single-process')
                chrome_options.add_argument('--disable-background-networking')
                chrome_options.add_argument('--disable-background-timer-throttling')
                chrome_options.add_argument('--disable-renderer-backgrounding')
                chrome_options.add_argument('--disable-backgrounding-occluded-windows')
                # Opciones adicionales para estabilidad
                chrome_options.add_argument('--disable-crash-reporter')
                chrome_options.add_argument('--disable-logging')
                chrome_options.add_argument('--log-level=3')  # Solo errores críticos
                chrome_options.add_argument('--disable-features=TranslateUI')
                chrome_options.add_argument('--disable-ipc-flooding-protection')
                chrome_options.add_argument('--disable-hang-monitor')
                chrome_options.add_argument('--disable-prompt-on-repost')
                chrome_options.add_argument('--disable-domain-reliability')
                chrome_options.add_argument('--disable-component-update')
                chrome_options.add_argument('--disable-sync')
                chrome_options.add_argument('--disable-default-apps')
                chrome_options.add_argument('--disable-features=VizDisplayCompositor')
                # Aumentar límites de memoria para evitar cierres
                chrome_options.add_argument('--max_old_space_size=4096')
                chrome_options.add_argument('--js-flags=--max-old-space-size=4096')
            else:
                logger.info("[SELENIUM] Modo con ventana visible")
            
            # Opciones para Linux sin desktop
            chrome_options.add_argument('--disable-blink-features=AutomationControlled')
            chrome_options.add_argument('--disable-extensions')
            chrome_options.add_argument('--window-size=1920,1080')
            # User-Agent completo de Chrome para que Liferay lo detecte como navegador real
            chrome_options.add_argument(
                '--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                'AppleWebKit/537.36 (KHTML, like Gecko) '
                'Chrome/142.0.0.0 Safari/537.36'
            )
            logger.info("[SELENIUM] User-Agent configurado como Chrome real")
            
            logger.info("[SELENIUM] Configurando preferencias de descarga...")
            # Preferencias para descargar PDFs
            download_dir = os.path.abspath("/tmp/siascafe_pdfs")
            os.makedirs(download_dir, exist_ok=True)
            logger.info(f"[SELENIUM] Directorio de descarga: {download_dir}")
            
            prefs = {
                "download.default_directory": download_dir,
                "download.prompt_for_download": False,
                "download.directory_upgrade": True,
                "plugins.always_open_pdf_externally": True
            }
            chrome_options.add_experimental_option("prefs", prefs)
            
            # Configurar proxy desde variables de entorno (si están disponibles)
            # El proxy-bridge maneja la autenticación, solo necesitamos apuntar a él
            proxy_url = os.getenv('HTTP_PROXY') or os.getenv('http_proxy')
            if proxy_url:
                logger.info(f"[SELENIUM] Configurando proxy para Chrome: {proxy_url}")
                chrome_options.add_argument(f'--proxy-server={proxy_url}')
            else:
                logger.info("[SELENIUM] No se detectó configuración de proxy en variables de entorno")
            
            # Configurar ChromeDriver: primero intentar usar el del sistema, luego webdriver-manager
            logger.info("[SELENIUM] Configurando ChromeDriver...")
            chromedriver_path = None
            
            # Intentar usar ChromeDriver del sistema (instalado en Dockerfile)
            system_chromedriver_paths = [
                '/usr/local/bin/chromedriver',
                '/usr/bin/chromedriver',
                'chromedriver'  # En PATH
            ]
            
            for path in system_chromedriver_paths:
                if os.path.exists(path) or path == 'chromedriver':
                    try:
                        # Verificar que es ejecutable
                        if path != 'chromedriver':
                            if os.access(path, os.X_OK):
                                chromedriver_path = path
                                logger.info(f"[SELENIUM] Usando ChromeDriver del sistema: {path}")
                                break
                        else:
                            # Verificar que chromedriver está en PATH
                            import shutil
                            chromedriver_bin = shutil.which('chromedriver')
                            if chromedriver_bin:
                                chromedriver_path = chromedriver_bin
                                logger.info(f"[SELENIUM] Usando ChromeDriver del PATH: {chromedriver_bin}")
                                break
                    except Exception as e:
                        logger.debug(f"[SELENIUM] No se pudo usar {path}: {e}")
                        continue
            
            # Si no se encontró ChromeDriver del sistema, usar webdriver-manager
            if not chromedriver_path:
                logger.info("[SELENIUM] ChromeDriver del sistema no encontrado, usando webdriver-manager...")
                try:
                    downloaded_path = ChromeDriverManager().install()
                    logger.info(f"[SELENIUM] webdriver-manager devolvió: {downloaded_path}")
                    
                    # webdriver-manager puede devolver un directorio o un archivo
                    if os.path.isdir(downloaded_path):
                        # Buscar el ejecutable chromedriver en el directorio
                        # Buscar primero en el directorio raíz
                        potential_paths = [
                            os.path.join(downloaded_path, 'chromedriver'),
                            os.path.join(downloaded_path, 'chromedriver-linux64', 'chromedriver'),
                        ]
                        
                        # También buscar recursivamente
                        for root, dirs, files in os.walk(downloaded_path):
                            for file in files:
                                # Solo archivos llamados exactamente 'chromedriver' (sin extensión)
                                # Ignorar archivos como THIRD_PARTY_NOTICES.chromedriver
                                if file == 'chromedriver' and '.' not in file:
                                    potential_path = os.path.join(root, file)
                                    # Verificar que es un archivo regular (no un directorio)
                                    if os.path.isfile(potential_path):
                                        # Ignorar si contiene THIRD_PARTY o NOTICES en el path
                                        if 'THIRD_PARTY' not in potential_path and 'NOTICES' not in potential_path:
                                            potential_paths.append(potential_path)
                        
                        # Probar cada path potencial
                        for path in potential_paths:
                            if os.path.exists(path) and os.path.isfile(path):
                                try:
                                    # Hacer ejecutable si no lo es
                                    if not os.access(path, os.X_OK):
                                        os.chmod(path, 0o755)
                                    # Verificar que ahora es ejecutable
                                    if os.access(path, os.X_OK):
                                        chromedriver_path = path
                                        logger.info(f"[SELENIUM] ChromeDriver ejecutable encontrado en: {chromedriver_path}")
                                        break
                                except Exception as e:
                                    logger.debug(f"[SELENIUM] No se pudo hacer ejecutable {path}: {e}")
                                    continue
                        
                        if not chromedriver_path:
                            raise Exception(f"No se encontró ejecutable chromedriver en {downloaded_path}. Archivos encontrados: {os.listdir(downloaded_path) if os.path.exists(downloaded_path) else 'N/A'}")
                    else:
                        # Es un archivo, verificar que sea el ejecutable correcto
                        if os.path.exists(downloaded_path) and os.path.isfile(downloaded_path):
                            # Verificar que no sea un archivo de documentación o texto
                            if 'THIRD_PARTY' in downloaded_path or 'NOTICES' in downloaded_path or downloaded_path.endswith('.txt') or downloaded_path.endswith('.md'):
                                raise Exception(f"webdriver-manager devolvió un archivo incorrecto (documentación): {downloaded_path}")
                            
                            # Intentar hacer ejecutable si no lo es
                            if not os.access(downloaded_path, os.X_OK):
                                os.chmod(downloaded_path, 0o755)
                            
                            chromedriver_path = downloaded_path
                            logger.info(f"[SELENIUM] ChromeDriver descargado: {chromedriver_path}")
                        else:
                            raise Exception(f"ChromeDriver descargado no es un archivo válido: {downloaded_path}")
                            
                except Exception as e:
                    logger.error(f"[SELENIUM] Error al configurar ChromeDriver con webdriver-manager: {e}")
                    import traceback
                    logger.error(traceback.format_exc())
                    raise
            
            # Crear servicio con el path correcto
            try:
                service = Service(chromedriver_path)
                logger.info(f"[SELENIUM] ChromeDriver configurado correctamente: {chromedriver_path}")
            except Exception as e:
                logger.error(f"[SELENIUM] Error al crear servicio ChromeDriver: {e}")
                raise
            
            logger.info("[SELENIUM] Inicializando driver de Chrome...")
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            logger.info("[SELENIUM] [OK] Driver de Chrome inicializado exitosamente")
            
            # Configurar timeouts más generosos para evitar desconexiones
            self.driver.implicitly_wait(15)
            # Tiempo de carga de página más generoso (la app es pesada)
            try:
                self.driver.set_page_load_timeout(120)  # Aumentado a 120 segundos
                # Timeout para scripts
                self.driver.set_script_timeout(60)
                logger.info("[SELENIUM] Timeouts configurados: implicit=15s, page_load=120s, script=60s")
            except Exception as e:
                logger.warning(f"[SELENIUM] No se pudo configurar timeouts: {e}")
            
            # Verificar que la sesión está activa
            try:
                self.driver.current_url
                logger.info("[SELENIUM] Sesión de Chrome verificada y activa")
            except Exception as e:
                logger.warning(f"[SELENIUM] Advertencia al verificar sesión inicial: {e}")
            
        except Exception as e:
            logger.error(f"[SELENIUM] [ERROR] No se pudo inicializar Chrome: {e}")
            import traceback
            logger.error(f"[SELENIUM] Traceback:\n{traceback.format_exc()}")
            logger.error("[SELENIUM] Asegúrate de tener Chrome instalado")
            logger.error("[SELENIUM] En Linux: sudo apt-get install google-chrome-stable")
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
    
    def generate_pdf(self, form_data: Dict, user_data: Dict) -> Optional[bytes]:
        """
        Genera un PDF usando Selenium para llenar el formulario y descargarlo
        
        Args:
            form_data: Datos del formulario (mapeados desde BD)
            user_data: Datos del usuario (etapa, edad, densidad, sombrío)
        
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
            
            # En lugar de esperar un tiempo fijo, esperar explícitamente
            # a que el portlet React principal esté montado.
            logger.info("[SELENIUM] Esperando a que se monte el portlet principal...")
            WebDriverWait(self.driver, 30).until(
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
        wait = WebDriverWait(self.driver, 30)
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
    
    def _wait_for_pdf(self, timeout: int = 60) -> Optional[bytes]:
        """Espera a que aparezca el botón 'Descargar PDF', hace clic y descarga el PDF"""
        try:
            logger.info("[SIASCAFE] Esperando a que aparezca el botón 'Descargar PDF'...")
            wait = WebDriverWait(self.driver, timeout)
            
            # Esperar a que aparezca el botón "Descargar PDF"
            # El botón es un <span> con role="button" que contiene el texto "Descargar PDF"
            try:
                # Buscar el span con role="button" que contiene "Descargar PDF"
                download_button = wait.until(
                    EC.element_to_be_clickable(
                        (By.XPATH, "//span[@role='button' and contains(., 'Descargar PDF')]")
                    )
                )
                logger.info("[SIASCAFE] [OK] Botón 'Descargar PDF' encontrado por texto")
            except TimeoutException:
                # Fallback: buscar por el ícono AssignmentReturnedIcon y encontrar el span padre
                try:
                    logger.info("[SIASCAFE] Buscando botón por ícono AssignmentReturnedIcon...")
                    icon = wait.until(
                        EC.presence_of_element_located(
                            (By.CSS_SELECTOR, "svg[data-testid='AssignmentReturnedIcon']")
                        )
                    )
                    # Encontrar el span padre con role="button" que contiene el ícono
                    download_button = icon.find_element(By.XPATH, "./ancestor::span[@role='button']")
                    logger.info("[SIASCAFE] [OK] Botón 'Descargar PDF' encontrado por ícono")
                except Exception as e:
                    logger.error(f"[SIASCAFE] [ERROR] No se pudo encontrar el botón 'Descargar PDF': {e}")
                    # Guardar HTML para diagnóstico
                    try:
                        with open('/tmp/siascafe_page_before_download.html', 'w', encoding='utf-8') as f:
                            f.write(self.driver.page_source)
                        logger.info("[SIASCAFE] HTML guardado en /tmp/siascafe_page_before_download.html para diagnóstico")
                    except:
                        pass
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
            download_dir = "/tmp/siascafe_pdfs"
            os.makedirs(download_dir, exist_ok=True)
            
            logger.info(f"[SIASCAFE] Esperando descarga del PDF en {download_dir} (hasta {timeout} segundos)...")
            start_time = time.time()
            check_interval = 1  # Verificar cada segundo
            initial_files = set()
            if os.path.exists(download_dir):
                initial_files = set([f for f in os.listdir(download_dir) if f.endswith('.pdf')])
            
            while time.time() - start_time < timeout:
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
                if elapsed < timeout:
                    time.sleep(check_interval)
                    if int(elapsed) % 5 == 0:  # Log cada 5 segundos
                        logger.info(f"[SIASCAFE] Esperando descarga del PDF... ({int(elapsed)}/{timeout} segundos)")
            
            logger.error(f"[SIASCAFE] Timeout de {timeout} segundos alcanzado esperando descarga del PDF")
            
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
