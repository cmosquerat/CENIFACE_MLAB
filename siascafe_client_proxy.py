"""
Modificación de siascafe_client.py para usar proxy
Agregar estas líneas al inicio de _setup_driver en siascafe_client.py
"""

# Ejemplo de cómo modificar _setup_driver para usar proxy:

def _setup_driver(self):
    """Configura el driver de Chrome con proxy"""
    # ... código existente ...
    
    # AGREGAR ESTO si tienes un proxy HTTP:
    proxy_url = os.getenv('SIASCAFE_PROXY_URL', '')  # Ej: http://proxy-colombia.com:8080
    if proxy_url:
        logger.info(f"[SELENIUM] Configurando proxy: {proxy_url}")
        chrome_options.add_argument(f'--proxy-server={proxy_url}')
    
    # ... resto del código ...
    
    self.driver = webdriver.Chrome(service=service, options=chrome_options)
    # ... resto del código ...

