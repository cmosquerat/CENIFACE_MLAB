FROM ubuntu:22.04

# Evitar prompts interactivos durante la instalación
ENV DEBIAN_FRONTEND=noninteractive

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    python3-venv \
    wget \
    curl \
    gnupg \
    unzip \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Instalar Google Chrome
RUN wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | apt-key add - \
    && echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google-chrome.list \
    && apt-get update \
    && apt-get install -y google-chrome-stable \
    && rm -rf /var/lib/apt/lists/*

# Instalar ChromeDriver compatible con Chrome instalado
RUN CHROME_VERSION=$(google-chrome --version 2>/dev/null | grep -oE '[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+' | head -1) \
    && CHROME_MAJOR=$(echo $CHROME_VERSION | cut -d. -f1) \
    && echo "Chrome versión instalada: $CHROME_VERSION (Major: $CHROME_MAJOR)" \
    && CHROMEDRIVER_VERSION=$(curl -sS "https://googlechromelabs.github.io/chrome-for-testing/last-known-good-versions-with-downloads.json" 2>/dev/null | grep -oE '"version":"[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+"' | head -1 | cut -d'"' -f4) \
    && if [ -z "$CHROMEDRIVER_VERSION" ]; then \
        CHROMEDRIVER_VERSION=$(curl -sS "https://chromedriver.storage.googleapis.com/LATEST_RELEASE_${CHROME_MAJOR}" 2>/dev/null || curl -sS "https://chromedriver.storage.googleapis.com/LATEST_RELEASE" 2>/dev/null || echo ""); \
    fi \
    && if [ -z "$CHROMEDRIVER_VERSION" ]; then \
        echo "No se pudo determinar versión de ChromeDriver, usando última conocida"; \
        CHROMEDRIVER_VERSION="latest"; \
    fi \
    && echo "Instalando ChromeDriver versión: $CHROMEDRIVER_VERSION" \
    && (wget -q -O /tmp/chromedriver.zip "https://storage.googleapis.com/chrome-for-testing-public/${CHROMEDRIVER_VERSION}/linux64/chromedriver-linux64.zip" 2>/dev/null \
    || wget -q -O /tmp/chromedriver.zip "https://storage.googleapis.com/chrome-for-testing-public/${CHROMEDRIVER_VERSION}/linux64/chromedriver-linux64.zip" 2>/dev/null \
    || wget -q -O /tmp/chromedriver.zip "http://chromedriver.storage.googleapis.com/${CHROMEDRIVER_VERSION}/chromedriver_linux64.zip" 2>/dev/null) \
    && unzip -q /tmp/chromedriver.zip -d /tmp/ \
    && find /tmp -name "chromedriver" -type f ! -name "*.txt" ! -name "*.md" ! -path "*THIRD_PARTY*" -exec mv {} /usr/local/bin/chromedriver \; \
    && rm -rf /tmp/chromedriver.zip /tmp/chromedriver-linux64* \
    && chmod +x /usr/local/bin/chromedriver \
    && /usr/local/bin/chromedriver --version && echo "ChromeDriver instalado correctamente en /usr/local/bin/chromedriver"

# Crear directorio de trabajo
WORKDIR /app

# Copiar requirements primero para aprovechar cache de Docker
COPY requirements.txt .

# Instalar dependencias de Python
RUN pip3 install --no-cache-dir -r requirements.txt

# Copiar script de entrada primero (antes de COPY . . para evitar que se ignore)
COPY docker-entrypoint.sh /docker-entrypoint.sh

# Copiar código de la aplicación
COPY . .

# Crear directorios necesarios
RUN mkdir -p static/pdfs static/css static/js static/images templates data

# Variables de entorno por defecto
ENV FLASK_APP=app.py
ENV FLASK_ENV=production
ENV PORT=5000
ENV DEBUG=False
ENV HOST=0.0.0.0

# Exponer puerto interno (el mapeo externo se hace en docker run)
EXPOSE 5000

# Usuario no root (mejores prácticas de seguridad)
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app

# Dar permisos al script de entrada
RUN chmod +x /docker-entrypoint.sh && chown appuser:appuser /docker-entrypoint.sh

USER appuser

# Comando de inicio
ENTRYPOINT ["/docker-entrypoint.sh"]
CMD ["python3", "app.py"]

