#!/usr/bin/env python
"""Diagnóstico de la aplicación web"""
import os
import sys

print("=" * 60)
print("DIAGNÓSTICO DE APLICACIÓN WEB")
print("=" * 60)
print()

# Verificar archivos
files_to_check = [
    'app.py',
    'templates/index.html',
    'static/css/style.css',
    'static/js/app.js',
    'database.py',
    'data_mapper.py',
    'siascafe_client.py',
    'multilab.db'
]

print("1. Verificando archivos...")
for file in files_to_check:
    exists = os.path.exists(file)
    status = "OK" if exists else "MISSING"
    print(f"   [{status}] {file}")

print()
print("2. Verificando importaciones...")
try:
    from flask import Flask
    print("   [OK] Flask")
except ImportError as e:
    print(f"   [ERROR] Flask: {e}")
    sys.exit(1)

try:
    from database import DatabaseManager
    print("   [OK] database")
except ImportError as e:
    print(f"   [ERROR] database: {e}")

try:
    from data_mapper import DataMapper
    print("   [OK] data_mapper")
except ImportError as e:
    print(f"   [ERROR] data_mapper: {e}")

try:
    from siascafe_client import SIASCAFEClient
    print("   [OK] siascafe_client")
except ImportError as e:
    print(f"   [ERROR] siascafe_client: {e}")

print()
print("3. Verificando template...")
try:
    from flask import Flask, render_template
    app_test = Flask(__name__)
    with app_test.app_context():
        try:
            render_template('index.html')
            print("   [OK] Template se puede renderizar")
        except Exception as e:
            print(f"   [ERROR] Error al renderizar template: {e}")
except Exception as e:
    print(f"   [ERROR] Error: {e}")

print()
print("=" * 60)
print("DIAGNÓSTICO COMPLETADO")
print("=" * 60)

