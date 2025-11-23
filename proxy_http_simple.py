#!/usr/bin/env python3
"""
Proxy HTTP simple para SIASCAFE
Ejecutar en un servidor VPS en Colombia
"""
from http.server import HTTPServer, BaseHTTPRequestHandler
import urllib.request
import urllib.parse
import logging
import sys

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ProxyHandler(BaseHTTPRequestHandler):
    """Manejador de proxy HTTP simple"""
    
    def do_GET(self):
        """Maneja peticiones GET"""
        self._handle_request()
    
    def do_POST(self):
        """Maneja peticiones POST"""
        self._handle_request()
    
    def do_PUT(self):
        """Maneja peticiones PUT"""
        self._handle_request()
    
    def do_DELETE(self):
        """Maneja peticiones DELETE"""
        self._handle_request()
    
    def _handle_request(self):
        """Maneja cualquier tipo de petición HTTP"""
        try:
            # Construir URL completa
            if self.path.startswith('/'):
                # Si es una ruta relativa, agregar dominio de SIASCAFE
                url = 'https://agroclima.cenicafe.org' + self.path
            else:
                url = self.path
            
            logger.info(f"Proxying request: {self.command} {url}")
            
            # Crear petición
            req = urllib.request.Request(url, method=self.command)
            
            # Copiar headers del cliente
            for header, value in self.headers.items():
                if header.lower() not in ['host', 'connection', 'content-length']:
                    req.add_header(header, value)
            
            # User-Agent para parecer navegador real
            req.add_header('User-Agent', 
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36')
            
            # Leer body si existe (POST, PUT, etc.)
            if self.command in ['POST', 'PUT']:
                content_length = int(self.headers.get('Content-Length', 0))
                if content_length > 0:
                    body = self.rfile.read(content_length)
                    req.data = body
            
            # Realizar petición
            with urllib.request.urlopen(req, timeout=30) as response:
                # Enviar respuesta al cliente
                self.send_response(response.getcode())
                
                # Copiar headers de respuesta
                for header, value in response.headers.items():
                    if header.lower() not in ['connection', 'transfer-encoding']:
                        self.send_header(header, value)
                
                self.end_headers()
                
                # Enviar contenido
                self.wfile.write(response.read())
                
            logger.info(f"Response: {response.getcode()} for {url}")
            
        except urllib.error.HTTPError as e:
            logger.error(f"HTTP Error {e.code}: {e.reason} for {self.path}")
            self.send_error(e.code, e.reason)
        except Exception as e:
            logger.error(f"Error proxying request: {e}")
            self.send_error(500, str(e))
    
    def log_message(self, format, *args):
        """Sobrescribir para usar nuestro logger"""
        logger.info(f"{self.address_string()} - {format % args}")


def run_proxy_server(port=8080, host='0.0.0.0'):
    """Inicia el servidor proxy"""
    server_address = (host, port)
    httpd = HTTPServer(server_address, ProxyHandler)
    
    logger.info(f"Proxy server iniciado en http://{host}:{port}")
    logger.info("Presiona Ctrl+C para detener")
    
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        logger.info("Deteniendo servidor proxy...")
        httpd.shutdown()


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Proxy HTTP simple para SIASCAFE')
    parser.add_argument('--port', type=int, default=8080, help='Puerto del proxy (default: 8080)')
    parser.add_argument('--host', type=str, default='0.0.0.0', help='Host del proxy (default: 0.0.0.0)')
    
    args = parser.parse_args()
    
    run_proxy_server(port=args.port, host=args.host)

