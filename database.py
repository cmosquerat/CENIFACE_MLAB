"""
Módulo para conexión y consultas a la base de datos multilab (SQLite)
"""
import sqlite3
from typing import Dict, Optional
from datetime import datetime
import logging
import os
from config import DB_PATH

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DatabaseManager:
    """Gestor de conexiones y consultas a la base de datos SQLite"""
    
    def __init__(self):
        self.db_path = DB_PATH
        self.connection = None
    
    def connect(self):
        """Establece conexión con la base de datos SQLite"""
        try:
            if not os.path.exists(self.db_path):
                logger.error(f"[DB] Base de datos no encontrada: {self.db_path}")
                logger.error("[DB] Ejecuta: python convert_mysql_to_sqlite.py")
                return False
            
            self.connection = sqlite3.connect(self.db_path)
            self.connection.row_factory = sqlite3.Row  # Para acceso tipo diccionario
            logger.info(f"[DB] Conexión exitosa a SQLite: {self.db_path}")
            return True
        except Exception as e:
            logger.error(f"[DB] Error al conectar a SQLite: {e}")
            logger.error(f"[DB] Ruta intentada: {self.db_path}")
            logger.error("[DB] Verifica:")
            logger.error("  1. Que el archivo de base de datos exista")
            logger.error("  2. Ejecuta: python convert_mysql_to_sqlite.py")
            return False
    
    def disconnect(self):
        """Cierra la conexión con la base de datos"""
        if self.connection:
            self.connection.close()
            logger.info("[DB] Conexión SQLite cerrada")
    
    def get_table_by_year(self, year: int, table_type: str = 'muestra') -> str:
        """
        Determina el nombre de la tabla según el año
        table_type: 'muestra', 'orden', 'solicitudes'
        """
        return f"{table_type}_{year}"
    
    def table_exists(self, table_name: str) -> bool:
        """Verifica si una tabla existe en SQLite"""
        if not self.connection:
            return False
        
        cursor = self.connection.cursor()
        try:
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name=?
            """, (table_name,))
            return cursor.fetchone() is not None
        finally:
            cursor.close()
    
    def find_muestra_by_codigo(self, codigo_lab: int, year: Optional[int] = None) -> Optional[Dict]:
        """
        Busca una muestra por su código de laboratorio.
        
        Si `year` es None, recorre todas las tablas de muestras (2010‑2030),
        como antes. Si `year` tiene valor, solo consulta las tablas
        `muestra_<year>` y `orden_<year>`, imitando el comportamiento
        original del script que usaba el año actual.
        """
        logger.info(f"[DB] Buscando muestra con código de laboratorio: {codigo_lab}")
        if year is not None:
            logger.info(f"[DB] Año forzado para la búsqueda: {year}")
        
        if not self.connection:
            logger.info("[DB] No hay conexión activa, intentando conectar...")
            if not self.connect():
                logger.error("[DB] No se pudo establecer conexión a la base de datos")
                return None
            logger.info("[DB] Conexión establecida exitosamente")
        
        cursor = self.connection.cursor()
        
        try:
            # Determinar rango de años a revisar
            if year is not None:
                years = [year]
            else:
                years = list(range(2010, 2031))
                logger.info(f"[DB] Buscando en tablas de muestras desde 2010 hasta 2030...")

            tables_checked = 0
            
            for year in years:
                table_name = self.get_table_by_year(year, 'muestra')
                
                # Verificar si la tabla existe
                if not self.table_exists(table_name):
                    if year % 5 == 0:  # Log cada 5 años para no saturar
                        logger.debug(f"[DB] Tabla {table_name} no existe, continuando...")
                    tables_checked += 1
                    continue
                
                logger.debug(f"[DB] Verificando tabla {table_name}...")
                tables_checked += 1
                
                # Buscar la muestra
                query = f"""
                    SELECT * FROM {table_name} 
                    WHERE codigo = ?
                    LIMIT 1
                """
                cursor.execute(query, (codigo_lab,))
                row = cursor.fetchone()
                
                if row:
                    # Convertir Row a diccionario
                    muestra = dict(row)
                    logger.info(f"[DB] [OK] Muestra encontrada en tabla {table_name} (año {year})")
                    logger.info(f"[DB]   - Código muestra: {muestra.get('codigo')}")
                    logger.info(f"[DB]   - Referencia: {muestra.get('referencia', 'N/A')}")
                    logger.info(f"[DB]   - Orden asociada: {muestra.get('orden')}")
                    
                    # Buscar la orden asociada
                    logger.info(f"[DB] Buscando orden {muestra['orden']} en tabla orden_{year}...")
                    orden = self.find_orden_by_codigo(muestra['orden'], year)
                    
                    if orden:
                        logger.info(f"[DB] [OK] Orden encontrada")
                        logger.info(f"[DB]   - Código finca: {orden.get('codigo_finca')}")
                        logger.info(f"[DB]   - Código propietario: {orden.get('codigo_propietario')}")
                    else:
                        logger.warning(f"[DB] [ADVERTENCIA] Orden {muestra['orden']} no encontrada")
                    
                    # Buscar información adicional de catálogos
                    finca_info = None
                    cliente_solicitante_info = None
                    cliente_propietario_info = None
                    municipio_info = None
                    departamento_info = None
                    textura_info = None
                    
                    if orden:
                        if orden.get('codigo_finca'):
                            logger.info(f"[DB] Buscando información de finca {orden['codigo_finca']}...")
                            finca_info = self.get_finca_info(orden['codigo_finca'])
                            if finca_info:
                                logger.info(f"[DB] [OK] Finca encontrada: {finca_info.get('nombre', 'N/A')}")
                        
                        # Solicitante (quién pide el análisis)
                        if orden.get('codigo_solicitante'):
                            logger.info(f"[DB] Buscando información de solicitante {orden['codigo_solicitante']}...")
                            cliente_solicitante_info = self.get_cliente_info(orden['codigo_solicitante'])
                            if cliente_solicitante_info:
                                logger.info(f"[DB] [OK] Solicitante encontrado: {cliente_solicitante_info.get('nombre', 'N/A')}")

                        # Propietario de la finca (puede ser distinto del solicitante)
                        if orden.get('codigo_propietario'):
                            logger.info(f"[DB] Buscando información de propietario {orden['codigo_propietario']}...")
                            cliente_propietario_info = self.get_cliente_info(orden['codigo_propietario'])
                            if cliente_propietario_info:
                                logger.info(f"[DB] [OK] Propietario encontrado: {cliente_propietario_info.get('nombre', 'N/A')}")
                    
                    if finca_info:
                        if finca_info.get('municipio'):
                            logger.info(f"[DB] Buscando municipio {finca_info['municipio']}...")
                            municipio_info = self.get_municipio_info(finca_info['municipio'])
                            if municipio_info:
                                logger.info(f"[DB] [OK] Municipio encontrado: {municipio_info.get('nombre', 'N/A')}")
                        
                        if finca_info.get('departamento'):
                            logger.info(f"[DB] Buscando departamento {finca_info['departamento']}...")
                            departamento_info = self.get_departamento_info(finca_info['departamento'])
                            if departamento_info:
                                logger.info(f"[DB] [OK] Departamento encontrado: {departamento_info.get('nombre', 'N/A')}")
                    
                    if muestra.get('textura'):
                        logger.info(f"[DB] Buscando textura {muestra['textura']}...")
                        textura_info = self.get_textura_info(muestra['textura'])
                        if textura_info:
                            logger.info(f"[DB] [OK] Textura encontrada: {textura_info.get('nombre', 'N/A')}")
                    
                    logger.info(f"[DB] [OK] Datos completos obtenidos para muestra {codigo_lab}")
                    
                    return {
                        'muestra': muestra,
                        'orden': orden,
                        'finca': finca_info,
                        'cliente_solicitante': cliente_solicitante_info,
                        'cliente_propietario': cliente_propietario_info,
                        'municipio': municipio_info,
                        'departamento': departamento_info,
                        'textura': textura_info,
                        'year': year
                    }
            
            logger.warning(f"[DB] [ERROR] No se encontró muestra con código {codigo_lab} después de revisar {tables_checked} tablas")
            return None
            
        except Exception as e:
            logger.error(f"[DB] Error al buscar muestra: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return None
        finally:
            cursor.close()
    
    def find_orden_by_codigo(self, codigo_orden: int, year: int) -> Optional[Dict]:
        """Busca una orden por su código"""
        if not self.connection:
            return None
        
        cursor = self.connection.cursor()
        
        try:
            table_name = self.get_table_by_year(year, 'orden')
            if not self.table_exists(table_name):
                return None
            
            query = f"SELECT * FROM {table_name} WHERE codigo = ? LIMIT 1"
            cursor.execute(query, (codigo_orden,))
            row = cursor.fetchone()
            if row:
                return dict(row)
            return None
        except Exception as e:
            logger.error(f"[DB] Error al buscar orden: {e}")
            return None
        finally:
            cursor.close()
    
    def get_finca_info(self, codigo_finca: int) -> Optional[Dict]:
        """Obtiene información de una finca"""
        if not self.connection:
            return None
        
        cursor = self.connection.cursor()
        
        try:
            query = "SELECT * FROM finca WHERE codigo = ? LIMIT 1"
            cursor.execute(query, (codigo_finca,))
            row = cursor.fetchone()
            if row:
                return dict(row)
            return None
        except Exception as e:
            logger.error(f"[DB] Error al obtener finca: {e}")
            return None
        finally:
            cursor.close()
    
    def get_cliente_info(self, codigo_cliente: int) -> Optional[Dict]:
        """Obtiene información de un cliente"""
        if not self.connection:
            return None
        
        cursor = self.connection.cursor()
        
        try:
            query = "SELECT * FROM cliente WHERE codigo = ? LIMIT 1"
            cursor.execute(query, (codigo_cliente,))
            row = cursor.fetchone()
            if row:
                return dict(row)
            return None
        except Exception as e:
            logger.error(f"[DB] Error al obtener cliente: {e}")
            return None
        finally:
            cursor.close()
    
    def get_municipio_info(self, codigo_municipio: int) -> Optional[Dict]:
        """Obtiene información de un municipio"""
        if not self.connection:
            return None
        
        cursor = self.connection.cursor()
        
        try:
            # SQLite usa codigo_municipio como nombre de columna
            query = "SELECT * FROM municipios WHERE codigo_municipio = ? LIMIT 1"
            cursor.execute(query, (codigo_municipio,))
            row = cursor.fetchone()
            if row:
                return dict(row)
            return None
        except Exception as e:
            logger.error(f"[DB] Error al obtener municipio: {e}")
            return None
        finally:
            cursor.close()
    
    def get_departamento_info(self, codigo_departamento: int) -> Optional[Dict]:
        """Obtiene información de un departamento"""
        if not self.connection:
            return None
        
        cursor = self.connection.cursor()
        
        try:
            query = "SELECT * FROM departamentos WHERE codigo = ? LIMIT 1"
            cursor.execute(query, (codigo_departamento,))
            row = cursor.fetchone()
            if row:
                return dict(row)
            return None
        except Exception as e:
            logger.error(f"[DB] Error al obtener departamento: {e}")
            return None
        finally:
            cursor.close()
    
    def get_textura_info(self, codigo_textura: int) -> Optional[Dict]:
        """Obtiene información de textura"""
        if not self.connection:
            return None
        
        cursor = self.connection.cursor()
        
        try:
            query = "SELECT * FROM textura WHERE codigo = ? LIMIT 1"
            cursor.execute(query, (codigo_textura,))
            row = cursor.fetchone()
            if row:
                return dict(row)
            return None
        except Exception as e:
            logger.error(f"[DB] Error al obtener textura: {e}")
            return None
        finally:
            cursor.close()
