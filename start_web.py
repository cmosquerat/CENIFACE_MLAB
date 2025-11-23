#!/usr/bin/env python
"""
Script de inicio rápido para la aplicación web
"""
import os
import sys

def check_dependencies():
    """Verifica que las dependencias estén instaladas"""
    try:
        import flask
        import selenium
        print("✓ Dependencias verificadas")
        return True
    except ImportError as e:
        print(f"✗ Error: Falta dependencia: {e}")
        print("Ejecuta: pip install -r requirements.txt")
        return False

def check_database():
    """Verifica que la base de datos exista"""
    if os.path.exists('multilab.db'):
        print("✓ Base de datos encontrada")
        return True
    else:
        print("✗ Error: No se encontró multilab.db")
        print("Asegúrate de tener la base de datos SQLite en el directorio raíz")
        return False

def check_directories():
    """Verifica y crea directorios necesarios"""
    dirs = ['static/pdfs', 'static/css', 'static/js', 'static/images', 'templates']
    for dir_path in dirs:
        os.makedirs(dir_path, exist_ok=True)
    print("✓ Directorios verificados")

if __name__ == '__main__':
    print("=" * 60)
    print("Multilab Agroanalítica - Verificación de Sistema")
    print("=" * 60)
    print()
    
    if not check_dependencies():
        sys.exit(1)
    
    check_directories()
    
    if not check_database():
        print("\n⚠ Advertencia: La base de datos no existe, pero puedes continuar")
        print("   (algunas funcionalidades no estarán disponibles)")
    
    print()
    print("=" * 60)
    print("Iniciando servidor web...")
    print("Abre tu navegador en: http://localhost:5000")
    print("Presiona Ctrl+C para detener el servidor")
    print("=" * 60)
    print()
    
    # Importar y ejecutar app
    from app import app
    app.run(debug=True, host='0.0.0.0', port=5000)

