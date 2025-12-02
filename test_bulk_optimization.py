#!/usr/bin/env python
"""
Script de prueba para procesamiento masivo optimizado (ciclo con 'LIMPIAR DATOS')
Rango: 9017 - 9030
Año: 2025
"""
import os
import time
import logging
from datetime import datetime
from database import DatabaseManager
from data_mapper import DataMapper
from siascafe_client import SIASCAFEClient

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("TEST_BULK")

def main():
    # Configuración del rango
    start_code = 9017
    end_code = 9030
    year = 2025
    
    # Datos fijos de usuario para la prueba
    user_data_template = {
        "etapa": 0,      # CRECIMIENTO
        "edad": 0,
        "densidad": 4444,
        "sombrío": 0
    }

    codes = list(range(start_code, end_code + 1))
    logger.info(f"Iniciando prueba masiva para {len(codes)} muestras: {start_code} - {end_code} (Año {year})")

    # 1. Inicializar Base de Datos
    db = DatabaseManager()
    if not db.connect():
        logger.error("No se pudo conectar a la base de datos")
        return

    # 2. Inicializar Cliente Selenium (UNA SOLA VEZ)
    # keep_browser_open=True para ver qué pasa si falla
    client = SIASCAFEClient(headless=False, keep_browser_open=True)
    
    try:
        first_run = True
        
        for code in codes:
            logger.info(f"\n>>> Procesando muestra {code}...")
            
            # a. Buscar datos en BD
            db_data = db.find_muestra_by_codigo(code, year=year)
            if not db_data:
                logger.warning(f"Muestra {code} no encontrada en BD (año {year}), saltando...")
                continue
            
            # b. Preparar datos
            validated_user = DataMapper.validate_user_data(user_data_template)
            siascafe_data = DataMapper.map_to_siascafe_format(db_data, validated_user)
            
            # c. Preparar formulario (Navegar o Limpiar)
            navigate = False
            if first_run:
                navigate = True
                first_run = False
            else:
                # Intentar limpiar datos
                # Si no se puede limpiar (ej. estamos en otra página), forzar navegación
                if not client.reset_form():
                    logger.warning("No se pudo limpiar formulario, recargando página...")
                    navigate = True
            
            # d. Generar PDF
            pdf_bytes = client.generate_pdf(siascafe_data, validated_user, navigate=navigate)
            
            if pdf_bytes:
                filename = f"resultado_{code}_{datetime.now().strftime('%H%M%S')}.pdf"
                filepath = os.path.join(os.getcwd(), filename)
                with open(filepath, "wb") as f:
                    f.write(pdf_bytes)
                logger.info(f"[SUCCESS] PDF guardado: {filepath}")
            else:
                logger.error(f"[FAILURE] No se generó PDF para {code}")
                # Si falló, forzar navegación en la siguiente para asegurar estado limpio
                first_run = True 

            # Pequeña pausa entre ciclos
            time.sleep(1)

    except KeyboardInterrupt:
        logger.info("Prueba interrumpida por usuario")
    except Exception as e:
        logger.error(f"Error fatal en el ciclo: {e}")
        import traceback
        logger.error(traceback.format_exc())
    finally:
        db.disconnect()
        # client se cierra solo al salir si keep_browser_open=False, 
        # pero aquí lo pusimos True para debug. 
        # Si quieres cerrar al final:
        # client.driver.quit()

if __name__ == "__main__":
    main()

