# Soluciones de Proxy para SIASCAFE

La página `agroclima.cenicafe.org` parece estar bloqueando conexiones desde fuera de Colombia. Aquí hay varias soluciones económicas y fáciles de implementar.

## Opción 1: Proxy HTTP Simple con Python (Gratis)

Usar un servidor proxy HTTP simple en un servidor VPS en Colombia.

### Requisitos:
- VPS en Colombia (DigitalOcean, Linode, Vultr tienen opciones desde $5/mes)
- O usar un servidor existente en Colombia

### Implementación:

```python
# proxy_server.py (ejecutar en servidor en Colombia)
from http.server import HTTPServer, BaseHTTPRequestHandler
import urllib.request
import urllib.parse

class ProxyHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            url = self.path[1:]  # Remover el /
            if not url.startswith('http'):
                url = 'https://agroclima.cenicafe.org' + self.path
            
            req = urllib.request.Request(url)
            req.add_header('User-Agent', 'Mozilla/5.0')
            
            with urllib.request.urlopen(req) as response:
                self.send_response(200)
                self.send_header('Content-type', response.headers.get('Content-type', 'text/html'))
                self.end_headers()
                self.wfile.write(response.read())
        except Exception as e:
            self.send_error(500, str(e))

if __name__ == '__main__':
    server = HTTPServer(('0.0.0.0', 8080), ProxyHandler)
    print("Proxy server running on port 8080")
    server.serve_forever()
```

## Opción 2: Usar Proxy HTTP Comercial Barato

### Servicios recomendados:

1. **Bright Data (Luminati)** - Tiene plan gratuito limitado
2. **Smartproxy** - Desde $14/mes, proxies residenciales
3. **ProxyMesh** - Desde $30/mes, proxies rotativos
4. **Oxylabs** - Caro pero confiable

### Implementación en código:

```python
# En siascafe_client.py
import requests

PROXY_URL = "http://usuario:password@proxy-colombia.com:8080"

proxies = {
    'http': PROXY_URL,
    'https': PROXY_URL
}

# Para Selenium
chrome_options.add_argument('--proxy-server=http://proxy-colombia.com:8080')
```

## Opción 3: VPN Barata con IP Colombiana

### Servicios recomendados:

1. **NordVPN** - Tiene servidores en Colombia, ~$3-4/mes
2. **Surfshark** - Más barato, ~$2/mes
3. **ExpressVPN** - Más caro pero rápido

### Implementación:

```bash
# Instalar OpenVPN en el servidor
sudo apt-get install openvpn

# Configurar VPN
# Descargar archivos de configuración del proveedor VPN
# Conectar antes de ejecutar Docker
```

## Opción 4: Proxy SOCKS5 con SSH Tunnel (Gratis si tienes servidor)

Si tienes acceso a un servidor en Colombia:

```bash
# Crear túnel SSH
ssh -D 1080 -N usuario@servidor-colombia.com

# Usar en Docker
docker run ... -e HTTP_PROXY=socks5://host.docker.internal:1080 ...
```

## Opción 5: Servicio de Proxy Residencial Barato

**Webshare.io** - Proxies residenciales desde $2.99/mes
- Tiene IPs de Colombia
- Fácil de integrar
- API simple

## Recomendación: Proxy HTTP Simple (Opción 1)

La opción más económica y fácil es crear un proxy HTTP simple en un VPS pequeño en Colombia.

### Pasos:

1. **Contratar VPS en Colombia** (DigitalOcean, Vultr, etc.)
2. **Instalar proxy simple** (código incluido abajo)
3. **Configurar aplicación** para usar el proxy

### Costo estimado:
- VPS pequeño: $5-6/mes
- Total: ~$5-6/mes

## Implementación Recomendada

Ver archivo `proxy_http_simple.py` para implementación completa.

