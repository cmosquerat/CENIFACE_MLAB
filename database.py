"""
Módulo para conexión y consultas a la base de datos multilab (SQLite o MySQL)
"""
import sqlite3
from typing import Dict, Optional
from datetime import datetime
import logging
import os
from config import (
    USE_MYSQL, DB_TYPE, DB_PATH,
    DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, DB_NAME
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Importar MySQL connector solo si se va a usar MySQL
mysql_connector = None
if USE_MYSQL:
    try:
        import mysql.connector
        from mysql.connector import Error as MySQLError
        mysql_connector = mysql.connector
        logger.info("[DB] MySQL connector importado correctamente")
    except ImportError as e:
        logger.error(f"[DB] ERROR: No se pudo importar mysql.connector: {e}")
        logger.error("[DB] Instala con: pip install mysql-connector-python")
        USE_MYSQL = False


class DatabaseManager:
    """Gestor de conexiones y consultas a la base de datos (SQLite o MySQL)"""
    
    def __init__(self):
        self.db_type = DB_TYPE
        self.use_mysql = USE_MYSQL
        self.connection = None
        
        if self.use_mysql:
            self.db_host = DB_HOST
            self.db_port = int(DB_PORT)
            self.db_user = DB_USER
            self.db_password = DB_PASSWORD
            self.db_name = DB_NAME
            logger.info(f"[DB] Configurado para usar MySQL: {self.db_host}:{self.db_port}/{self.db_name}")
        else:
            self.db_path = DB_PATH
            logger.info(f"[DB] Configurado para usar SQLite: {self.db_path}")
    
    def connect(self):
        """Establece conexión con la base de datos (MySQL o SQLite)"""
        try:
            if self.use_mysql:
                return self._connect_mysql()
            else:
                return self._connect_sqlite()
        except Exception as e:
            logger.error(f"[DB] Error al conectar a {self.db_type}: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return False
    
    def _connect_mysql(self):
        """Establece conexión con MySQL"""
        try:
            logger.info(f"[DB] Intentando conectar a MySQL: {self.db_host}:{self.db_port}/{self.db_name}")
            self.connection = mysql.connector.connect(
                host=self.db_host,
                port=self.db_port,
                user=self.db_user,
                password=self.db_password,
                database=self.db_name,
                charset='utf8mb4',
                collation='utf8mb4_unicode_ci'
            )
            if self.connection.is_connected():
                db_info = self.connection.get_server_info()
                logger.info(f"[DB] ✓ Conexión exitosa a MySQL Server versión {db_info}")
                logger.info(f"[DB] ✓ Base de datos: {self.db_name}")
                logger.info(f"[DB] ✓ Host: {self.db_host}:{self.db_port}")
                logger.info(f"[DB] ✓ Usuario: {self.db_user}")
                return True
            return False
        except MySQLError as e:
            logger.error(f"[DB] Error al conectar a MySQL: {e}")
            logger.error(f"[DB] Host: {self.db_host}:{self.db_port}")
            logger.error(f"[DB] Database: {self.db_name}")
            logger.error(f"[DB] User: {self.db_user}")
            return False
    
    def _connect_sqlite(self):
        """Establece conexión con SQLite"""
        try:
            if not os.path.exists(self.db_path):
                logger.error(f"[DB] Base de datos SQLite no encontrada: {self.db_path}")
                logger.error("[DB] Verifica que el archivo exista en la ruta especificada")
                return False
            
            self.connection = sqlite3.connect(self.db_path)
            self.connection.row_factory = sqlite3.Row  # Para acceso tipo diccionario
            logger.info(f"[DB] ✓ Conexión exitosa a SQLite: {self.db_path}")
            return True
        except Exception as e:
            logger.error(f"[DB] Error al conectar a SQLite: {e}")
            logger.error(f"[DB] Ruta intentada: {self.db_path}")
            return False
    
    def disconnect(self):
        """Cierra la conexión con la base de datos"""
        if self.connection:
            if self.use_mysql:
                self.connection.close()
                logger.info("[DB] Conexión MySQL cerrada")
            else:
                self.connection.close()
                logger.info("[DB] Conexión SQLite cerrada")
    
    def get_table_by_year(self, year: int, table_type: str = 'muestra') -> str:
        """
        Determina el nombre de la tabla según el año
        table_type: 'muestra', 'orden', 'solicitudes'
        """
        return f"{table_type}_{year}"
    
    def table_exists(self, table_name: str) -> bool:
        """Verifica si una tabla existe"""
        if not self.connection:
            return False
        
        cursor = self.connection.cursor()
        try:
            if self.use_mysql:
                cursor.execute("""
                    SELECT COUNT(*) 
                    FROM information_schema.tables 
                    WHERE table_schema = %s AND table_name = %s
                """, (self.db_name, table_name))
                result = cursor.fetchone()
                return result[0] > 0 if result else False
            else:
                cursor.execute("""
                    SELECT name FROM sqlite_master 
                    WHERE type='table' AND name=?
                """, (table_name,))
                return cursor.fetchone() is not None
        except Exception as e:
            logger.error(f"[DB] Error al verificar tabla {table_name}: {e}")
            return False
        finally:
            cursor.close()
    
    def _execute_query(self, query: str, params: tuple = None):
        """Ejecuta una consulta y retorna el cursor"""
        cursor = self.connection.cursor(dictionary=True if self.use_mysql else None)
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
        return cursor
    
    def _row_to_dict(self, row):
        """Convierte una fila a diccionario"""
        if self.use_mysql:
            return dict(row) if isinstance(row, dict) else row
        else:
            return dict(row) if row else None
    
    def find_muestra_by_codigo(self, codigo_lab: int, year: Optional[int] = None) -> Optional[Dict]:
        """
        Busca una muestra por su código de laboratorio.
        
        Si `year` es None, recorre todas las tablas de muestras (2010‑2030),
        como antes. Si `year` tiene valor, solo consulta las tablas
        `muestra_<year>` y `orden_<year>`, imitando el comportamiento
        original del script que usaba el año actual.
        """
        logger.info(f"[DB] Buscando muestra con código de laboratorio: {codigo_lab}")
        logger.info(f"[DB] Tipo de BD: {self.db_type}")
        if year is not None:
            logger.info(f"[DB] Año forzado para la búsqueda: {year}")
        
        if not self.connection:
            logger.info("[DB] No hay conexión activa, intentando conectar...")
            if not self.connect():
                logger.error("[DB] No se pudo establecer conexión a la base de datos")
                return None
            logger.info("[DB] Conexión establecida exitosamente")
        
        cursor = self.connection.cursor(dictionary=True if self.use_mysql else None)
        
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
                
                # Buscar la muestra (adaptar sintaxis según BD)
                if self.use_mysql:
                    query = f"""
                        SELECT * FROM {table_name} 
                        WHERE codigo = %s
                        LIMIT 1
                    """
                    cursor.execute(query, (codigo_lab,))
                else:
                    query = f"""
                        SELECT * FROM {table_name} 
                        WHERE codigo = ?
                        LIMIT 1
                    """
                    cursor.execute(query, (codigo_lab,))
                
                row = cursor.fetchone()
                
                if row:
                    # Convertir Row a diccionario
                    muestra = self._row_to_dict(row)
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
        
        cursor = self.connection.cursor(dictionary=True if self.use_mysql else None)
        
        try:
            table_name = self.get_table_by_year(year, 'orden')
            if not self.table_exists(table_name):
                return None
            
            if self.use_mysql:
                query = f"SELECT * FROM {table_name} WHERE codigo = %s LIMIT 1"
            else:
                query = f"SELECT * FROM {table_name} WHERE codigo = ? LIMIT 1"
            
            cursor.execute(query, (codigo_orden,))
            row = cursor.fetchone()
            if row:
                return self._row_to_dict(row)
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
        
        cursor = self.connection.cursor(dictionary=True if self.use_mysql else None)
        
        try:
            if self.use_mysql:
                query = "SELECT * FROM finca WHERE codigo = %s LIMIT 1"
            else:
                query = "SELECT * FROM finca WHERE codigo = ? LIMIT 1"
            
            cursor.execute(query, (codigo_finca,))
            row = cursor.fetchone()
            if row:
                return self._row_to_dict(row)
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
        
        cursor = self.connection.cursor(dictionary=True if self.use_mysql else None)
        
        try:
            if self.use_mysql:
                query = "SELECT * FROM cliente WHERE codigo = %s LIMIT 1"
            else:
                query = "SELECT * FROM cliente WHERE codigo = ? LIMIT 1"
            
            cursor.execute(query, (codigo_cliente,))
            row = cursor.fetchone()
            if row:
                return self._row_to_dict(row)
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
        
        cursor = self.connection.cursor(dictionary=True if self.use_mysql else None)
        
        try:
            # SQLite usa codigo_municipio como nombre de columna
            if self.use_mysql:
                query = "SELECT * FROM municipios WHERE codigo_municipio = %s LIMIT 1"
            else:
                query = "SELECT * FROM municipios WHERE codigo_municipio = ? LIMIT 1"
            
            cursor.execute(query, (codigo_municipio,))
            row = cursor.fetchone()
            if row:
                return self._row_to_dict(row)
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
        
        cursor = self.connection.cursor(dictionary=True if self.use_mysql else None)
        
        try:
            if self.use_mysql:
                query = "SELECT * FROM departamentos WHERE codigo = %s LIMIT 1"
            else:
                query = "SELECT * FROM departamentos WHERE codigo = ? LIMIT 1"
            
            cursor.execute(query, (codigo_departamento,))
            row = cursor.fetchone()
            if row:
                return self._row_to_dict(row)
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
        
        cursor = self.connection.cursor(dictionary=True if self.use_mysql else None)
        
        try:
            if self.use_mysql:
                query = "SELECT * FROM textura WHERE codigo = %s LIMIT 1"
            else:
                query = "SELECT * FROM textura WHERE codigo = ? LIMIT 1"
            
            cursor.execute(query, (codigo_textura,))
            row = cursor.fetchone()
            if row:
                return self._row_to_dict(row)
            return None
        except Exception as e:
            logger.error(f"[DB] Error al obtener textura: {e}")
            return None
        finally:
            cursor.close()
