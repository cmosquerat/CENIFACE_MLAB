#!/usr/bin/env python
"""
Prueba directa con SQLite + Selenium (sin servidor Flask)

Uso:
    python test_selenium_sqlite.py              # usa 10766 CRECIMIENTO 0 4444 0
    python test_selenium_sqlite.py 10766 0 0 4444 0
"""

import sys
import os
import logging
from datetime import datetime

from database import DatabaseManager
from data_mapper import DataMapper
from siascafe_client import SIASCAFEClient


logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


def print_header(title: str):
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60 + "\n")


def parse_args(argv):
    """
    argv esperados:
        [codigo_lab, etapa, edad, densidad, sombrio]              # usa auto‑detección de año
        [codigo_lab, etapa, edad, densidad, sombrio, año]         # fuerza tablas muestra_año / orden_año
        Puede incluir --headless al final para modo headless
    """
    # Detectar flag --headless
    headless = "--headless" in argv
    if headless:
        argv = [arg for arg in argv if arg != "--headless"]
    
    if len(argv) == 0:
        # Valores por defecto solicitados (10766 CRECIMIENTO 0 4444 0), sin forzar año
        return {
            "codigo_lab": 10766,
            "etapa": 0,    # 0 = CRECIMIENTO
            "edad": 0,
            "densidad": 4444,
            "sombrío": 0,
            "year": None,
            "headless": headless,
        }

    if len(argv) not in (5, 6):
        print("Uso: python test_selenium_sqlite.py [codigo_lab etapa edad densidad sombrio [año]] [--headless]")
        print("  - etapa puede ser numérica (0,1,2) o texto: CRECIMIENTO, PRODUCCION, ZOCA")
        print("  - --headless: ejecuta en modo headless (sin ventana visible)")
        print("Ejemplos:")
        print("  python test_selenium_sqlite.py 10766 CRECIMIENTO 0 4444 0")
        print("  python test_selenium_sqlite.py 10766 CRECIMIENTO 0 4444 0 2015")
        print("  python test_selenium_sqlite.py 10766 CRECIMIENTO 0 4444 0 2015 --headless")
        sys.exit(1)

    def parse_etapa(raw):
        """
        Acepta etapa como:
          - código numérico: 0,1,2
          - texto: CRECIMIENTO, PRODUCCION/PRODUCCIÓN, ZOCA
        y la convierte al entero esperado por SIASCAFE.
        """
        txt = str(raw).strip().upper()
        # Normalizar acentos simples
        txt = txt.replace("Ó", "O")

        mapa = {
            "0": 0,
            "CRECIMIENTO": 0,
            "1": 1,
            "ZOCA": 1,
            "2": 2,
            "PRODUCCION": 2,
        }
        if txt in mapa:
            return mapa[txt]
        # Si no coincide, intentar parsear como entero directo
        return int(raw)

    try:
        codigo_lab = int(argv[0])
        etapa = parse_etapa(argv[1])
        edad = int(argv[2])
        densidad = int(argv[3])
        sombrio = int(argv[4])
        year = None
        if len(argv) == 6:
            year = int(argv[5])
    except ValueError:
        print("Error: parámetros inválidos. ")
        print("  codigo_lab, edad, densidad, sombrio y año (si se usa) deben ser numéricos.")
        print("  etapa puede ser 0/1/2 o CRECIMIENTO/PRODUCCION/ZOCA.")
        sys.exit(1)

    return {
        "codigo_lab": codigo_lab,
        "etapa": etapa,
        "edad": edad,
        "densidad": densidad,
        "sombrío": sombrio,
        "year": year,
        "headless": headless,
    }


def main():
    args = parse_args(sys.argv[1:])

    codigo_lab = args["codigo_lab"]
    forced_year = args.get("year")
    user_data = {
        "etapa": args["etapa"],
        "edad": args["edad"],
        "densidad": args["densidad"],
        "sombrío": args["sombrío"],
    }

    print_header("PRUEBA DIRECTA: SQLite + Selenium (SIN SERVIDOR)")
    print(f"Código de laboratorio: {codigo_lab}")
    if forced_year is not None:
        print(f"Año forzado para tablas muestra/orden: {forced_year}")
    print(f"Etapa: {user_data['etapa']}, Edad: {user_data['edad']}, "
          f"Densidad: {user_data['densidad']}, Sombrío: {user_data['sombrío']}")

    # 1. Conectar a la base de datos SQLite
    db = DatabaseManager()
    if not db.connect():
        print("[ERROR] No se pudo conectar a la base de datos SQLite")
        return

    try:
        # 2. Buscar muestra en la BD
        logger.info("[TEST] Buscando muestra en la base de datos...")
        db_data = db.find_muestra_by_codigo(codigo_lab, year=forced_year)
        if not db_data:
            print(f"[ERROR] No se encontró muestra con código de laboratorio {codigo_lab}")
            return

        # 3. Validar datos de usuario
        logger.info("[TEST] Validando datos de usuario...")
        validated_user = DataMapper.validate_user_data(user_data)

        # 4. Mapear datos al formato SIASCAFE
        logger.info("[TEST] Mapeando datos BD -> SIASCAFE...")
        siascafe_data = DataMapper.map_to_siascafe_format(db_data, validated_user)

        # 5. Inicializar cliente Selenium
        headless_mode = args.get("headless", False)
        if headless_mode:
            logger.info("[TEST] Inicializando cliente Selenium (modo HEADLESS)...")
        else:
            logger.info("[TEST] Inicializando cliente Selenium (con ventana visible)...")
        client = SIASCAFEClient(headless=headless_mode, keep_browser_open=False)

        # 6. Generar PDF
        logger.info("[TEST] Generando PDF en SIASCAFE (esto puede tardar algunos segundos)...")
        pdf_bytes = client.generate_pdf(siascafe_data, validated_user)

        if not pdf_bytes:
            print("[ERROR] No se pudo generar el PDF. Revisa los logs de [SELENIUM] y [SIASCAFE].")
            return

        # 7. Guardar PDF
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        out_name = f"resultado_{codigo_lab}_{timestamp}.pdf"
        out_path = os.path.join(os.getcwd(), out_name)

        with open(out_path, "wb") as f:
            f.write(pdf_bytes)

        print("\n[OK] PDF generado correctamente")
        print(f"[OK] Archivo guardado en: {out_path}")

    finally:
        db.disconnect()


if __name__ == "__main__":
    main()


