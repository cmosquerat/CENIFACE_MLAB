#!/bin/bash
# Script de instalación para Linux (servidor sin desktop)

echo "=========================================="
echo "  INSTALACIÓN BACKEND SIASCAFE"
echo "=========================================="

# Instalar Chrome
echo "Instalando Google Chrome..."
if [ -f /etc/debian_version ]; then
    # Debian/Ubuntu
    wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | sudo apt-key add -
    sudo sh -c 'echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google-chrome.list'
    sudo apt-get update
    sudo apt-get install -y google-chrome-stable
elif [ -f /etc/redhat-release ]; then
    # CentOS/RHEL
    sudo yum install -y google-chrome-stable
else
    echo "Por favor instala Chrome manualmente"
fi

# Crear entorno virtual
echo "Creando entorno virtual..."
python3 -m venv venv
source venv/bin/activate

# Instalar dependencias
echo "Instalando dependencias Python..."
pip install --upgrade pip
pip install -r requirements.txt

# Crear directorio para PDFs
echo "Creando directorios..."
mkdir -p /tmp/siascafe_pdfs

# Crear base de datos si no existe
if [ ! -f multilab.db ]; then
    echo "Convirtiendo MySQL a SQLite..."
    python convert_mysql_to_sqlite.py
fi

echo ""
echo "=========================================="
echo "  INSTALACIÓN COMPLETADA"
echo "=========================================="
echo ""
echo "Para ejecutar:"
echo "  source venv/bin/activate"
echo "  python app.py"
echo ""
echo "O en background:"
echo "  nohup python app.py > app.log 2>&1 &"

