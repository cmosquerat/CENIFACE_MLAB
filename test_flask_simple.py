#!/usr/bin/env python
"""Test simple de Flask"""
from flask import Flask

app = Flask(__name__)

@app.route('/')
def hello():
    return '<h1>Flask funciona correctamente!</h1><p>Si ves esto, Flask está funcionando.</p>'

@app.route('/test')
def test():
    return '<h1>Test endpoint</h1><p>Este endpoint también funciona.</p>'

if __name__ == '__main__':
    print("Iniciando servidor de prueba en http://127.0.0.1:5000")
    app.run(debug=True, host='127.0.0.1', port=5000)

