#!/bin/bash

# Script para configurar proxy HTTP simple en servidor VPS Colombia
# Ejecutar en el servidor VPS en Colombia

echo "=========================================="
echo "Configuración de Proxy HTTP para SIASCAFE"
echo "=========================================="

# Instalar Python3 si no está instalado
if ! command -v python3 &> /dev/null; then
    echo "Instalando Python3..."
    sudo apt-get update
    sudo apt-get install -y python3 python3-pip
fi

# Crear directorio para el proxy
mkdir -p ~/siascafe-proxy
cd ~/siascafe-proxy

# Crear archivo del proxy
cat > proxy_server.py << 'EOF'
#!/usr/bin/env python3
from http.server import HTTPServer, BaseHTTPRequestHandler
import urllib.request
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ProxyHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self._handle_request()
    
    def do_POST(self):
        self._handle_request()
    
    def _handle_request(self):
        try:
            url = 'https://agroclima.cenicafe.org' + self.path
            req = urllib.request.Request(url, method=self.command)
            req.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
            
            if self.command == 'POST':
                content_length = int(self.headers.get('Content-Length', 0))
                if content_length > 0:
                    req.data = self.rfile.read(content_length)
            
            with urllib.request.urlopen(req, timeout=30) as response:
                self.send_response(response.getcode())
                for header, value in response.headers.items():
                    if header.lower() not in ['connection', 'transfer-encoding']:
                        self.send_header(header, value)
                self.end_headers()
                self.wfile.write(response.read())
        except Exception as e:
            logger.error(f"Error: {e}")
            self.send_error(500, str(e))
    
    def log_message(self, format, *args):
        logger.info(f"{self.address_string()} - {format % args}")

if __name__ == '__main__':
    server = HTTPServer(('0.0.0.0', 8080), ProxyHandler)
    logger.info("Proxy server iniciado en puerto 8080")
    server.serve_forever()
EOF

chmod +x proxy_server.py

# Crear servicio systemd
sudo tee /etc/systemd/system/siascafe-proxy.service > /dev/null << EOF
[Unit]
Description=SIASCAFE HTTP Proxy Server
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$HOME/siascafe-proxy
ExecStart=/usr/bin/python3 $HOME/siascafe-proxy/proxy_server.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Habilitar y iniciar servicio
sudo systemctl daemon-reload
sudo systemctl enable siascafe-proxy.service
sudo systemctl start siascafe-proxy.service

# Verificar estado
sudo systemctl status siascafe-proxy.service

echo ""
echo "=========================================="
echo "Proxy configurado!"
echo "=========================================="
echo ""
echo "El proxy está disponible en:"
echo "  http://$(hostname -I | awk '{print $1}'):8080"
echo ""
echo "Comandos útiles:"
echo "  Ver logs:    sudo journalctl -u siascafe-proxy -f"
echo "  Reiniciar:   sudo systemctl restart siascafe-proxy"
echo "  Detener:     sudo systemctl stop siascafe-proxy"
echo ""

