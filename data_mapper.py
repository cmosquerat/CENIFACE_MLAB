"""
Módulo para mapear datos de la base de datos al formato de SIASCAFE
"""
import logging
import os
from typing import Dict, Optional
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DataMapper:
    """Mapea datos de la BD multilab al formato de SIASCAFE"""
    
    @staticmethod
    def map_to_siascafe_format(db_data: Dict, user_data: Dict) -> Dict:
        """
        Mapea los datos de la base de datos al formato esperado por SIASCAFE
        
        Args:
            db_data: Datos obtenidos de la base de datos (muestra, orden, finca, etc.)
            user_data: Datos proporcionados por el usuario (etapa, edad, densidad, sombrío)
        
        Returns:
            Diccionario con los datos en formato SIASCAFE
        """
        logger.info("[MAPPER] Iniciando mapeo de datos BD -> SIASCAFE")
        logger.info(f"[MAPPER] Datos del usuario: {user_data}")
        
        # Convertir Row objects a dicts si es necesario
        def to_dict(obj):
            """Convierte un objeto Row a dict si es necesario"""
            if obj is None:
                return {}
            if isinstance(obj, dict):
                return obj
            # Si es un Row object de SQLite
            try:
                return dict(obj)
            except (TypeError, AttributeError):
                return obj if obj else {}
        
        muestra = to_dict(db_data.get('muestra'))
        orden = to_dict(db_data.get('orden'))
        finca = to_dict(db_data.get('finca'))
        cliente_solicitante = to_dict(db_data.get('cliente_solicitante'))
        cliente_propietario = to_dict(db_data.get('cliente_propietario'))
        municipio = to_dict(db_data.get('municipio'))
        departamento = to_dict(db_data.get('departamento'))
        textura = to_dict(db_data.get('textura'))
        
        logger.info(f"[MAPPER] Datos disponibles:")
        logger.info(f"[MAPPER]   - Muestra: {'Sí' if muestra else 'No'}")
        logger.info(f"[MAPPER]   - Orden: {'Sí' if orden else 'No'}")
        logger.info(f"[MAPPER]   - Finca: {'Sí' if finca else 'No'}")
        logger.info(f"[MAPPER]   - Cliente solicitante: {'Sí' if cliente_solicitante else 'No'}")
        logger.info(f"[MAPPER]   - Cliente propietario: {'Sí' if cliente_propietario else 'No'}")
        logger.info(f"[MAPPER]   - Municipio: {'Sí' if municipio else 'No'}")
        logger.info(f"[MAPPER]   - Departamento: {'Sí' if departamento else 'No'}")
        logger.info(f"[MAPPER]   - Textura: {'Sí' if textura else 'No'}")
        
        # Fallbacks desde variables de entorno para cuando faltan tablas en SQLite
        default_nombre = os.getenv("SIASCAFE_DEFAULT_SOLICITANTE", "")
        default_departamento = os.getenv("SIASCAFE_DEFAULT_DEPARTAMENTO", "")
        default_municipio = os.getenv("SIASCAFE_DEFAULT_MUNICIPIO", "")
        default_finca = os.getenv("SIASCAFE_DEFAULT_FINCA", "")
        default_lote = os.getenv("SIASCAFE_DEFAULT_LOTE", "")
        
        # Preparar nombre del solicitante / propietario
        # En el script original de Selenium el campo "Solicitante"
        # se llenaba con el PROPIETARIO de la finca, no con el código
        # de solicitante. Replicamos ese comportamiento:
        nombre_solicitante = ""
        if cliente_propietario:
            nombre_solicitante = f"{cliente_propietario.get('nombre', '')} {cliente_propietario.get('apellido', '')}".strip()
            if not nombre_solicitante:
                nombre_solicitante = cliente_propietario.get('nombre', '')
        elif cliente_solicitante:
            nombre_solicitante = f"{cliente_solicitante.get('nombre', '')} {cliente_solicitante.get('apellido', '')}".strip()
            if not nombre_solicitante:
                nombre_solicitante = cliente_solicitante.get('nombre', '')
        if not nombre_solicitante and default_nombre:
            nombre_solicitante = default_nombre
        
        # Preparar departamento y municipio
        nombre_departamento = ""
        if departamento:
            nombre_departamento = departamento.get('nombre', '')
        elif municipio:
            # Intentar obtener del municipio si tiene referencia
            nombre_departamento = municipio.get('departamento', '')
        if not nombre_departamento and default_departamento:
            nombre_departamento = default_departamento
        
        nombre_municipio = ""
        if municipio:
            nombre_municipio = municipio.get('nombre', '')
        elif finca:
            nombre_municipio = finca.get('vereda', '')
        if not nombre_municipio and default_municipio:
            nombre_municipio = default_municipio
        
        # Preparar código de muestra y referencia
        codigo_muestra = str(muestra.get('codigo', '')) if muestra else ''
        referencia = muestra.get('referencia', '') if muestra else ''
        if not referencia and default_lote:
            referencia = default_lote
        
        # Preparar nombre de finca
        nombre_finca = ""
        if finca:
            nombre_finca = finca.get('nombre', '')
        if not nombre_finca and default_finca:
            nombre_finca = default_finca
        
        # Preparar fecha de muestreo
        def _parse_fecha(label: str, raw) -> str:
            """
            Normaliza una fecha a formato 'YYYY-MM-DD' estricto.
            Ignora valores '0000-00-00' o vacíos.
            """
            logger.info(f"[MAPPER] Parseando fecha desde {label}: valor='{raw}' (tipo={type(raw)})")
            
            if not raw:
                logger.warning(f"[MAPPER] {label} está vacío o es None")
                return ""
            
            # Si viene como datetime real
            if isinstance(raw, datetime):
                out = raw.strftime('%Y-%m-%d')
                logger.info(f"[MAPPER] [OK] {label} (datetime) -> fecha de muestreo: {out}")
                return out

            # Si viene como string
            if isinstance(raw, str):
                text = raw.strip()
                if not text:
                    logger.warning(f"[MAPPER] {label} es string vacío")
                    return ""
                
                # Tomar solo la parte de fecha (antes de cualquier espacio o hora)
                text = text.split()[0]
                
                # Descartar fechas inválidas de MySQL
                if text.startswith("0000-00-00"):
                    logger.warning(f"[MAPPER] {label} tiene fecha inválida MySQL '0000-00-00'")
                    return ""
                
                # Intentar parsear con formatos conocidos
                for fmt in ('%Y-%m-%d', '%Y/%m/%d', '%d/%m/%Y', '%Y-%m-%d %H:%M:%S'):
                    try:
                        dt = datetime.strptime(text, fmt)
                        out = dt.strftime('%Y-%m-%d')
                        logger.info(f"[MAPPER] [OK] {label}='{text}' (formato {fmt}) -> fecha normalizada: {out}")
                        return out
                    except ValueError:
                        continue
                
                # Si no se pudo parsear, log de error y devolver vacío
                logger.error(f"[MAPPER] [ERROR] No se pudo parsear {label}='{text}' con ningún formato conocido")
                return ""

            # Otros tipos: intentar convertir a string y parsear
            try:
                text = str(raw).strip()
                if text:
                    # Intentar parsear como si fuera string
                    text = text.split()[0]
                    for fmt in ('%Y-%m-%d', '%Y/%m/%d', '%d/%m/%Y'):
                        try:
                            dt = datetime.strptime(text, fmt)
                            out = dt.strftime('%Y-%m-%d')
                            logger.info(f"[MAPPER] [OK] {label} (convertido de {type(raw)})='{text}' -> fecha normalizada: {out}")
                            return out
                        except ValueError:
                            continue
                    logger.error(f"[MAPPER] [ERROR] No se pudo parsear {label}='{text}' después de convertir a string")
            except Exception as e:
                logger.error(f"[MAPPER] [ERROR] Error al convertir {label} a string: {e}")
            
            return ""

        # Estrategia:
        #  1) Intentar muestra.fecha_analisis
        #  2) Si no es válida, intentar orden.fecha_solicitud
        #  3) Si aún está vacío, usar fecha actual para no dejar el campo requerido vacío
        fecha_muestreo = ""
        if muestra and 'fecha_analisis' in muestra:
            fecha_muestreo = _parse_fecha('muestra.fecha_analisis', muestra.get('fecha_analisis'))
        
        if (not fecha_muestreo) and orden and 'fecha_solicitud' in orden:
            fecha_muestreo = _parse_fecha('orden.fecha_solicitud', orden.get('fecha_solicitud'))

        if not fecha_muestreo:
            # Fallback: fecha actual (mejor que dejar campo requerido vacío)
            fecha_muestreo = datetime.now().strftime('%Y-%m-%d')
            logger.info(f"[MAPPER] Usando fecha actual como fecha de muestreo por falta de datos válidos: {fecha_muestreo}")
        
        # Preparar valores químicos (convertir de string a float si es necesario)
        def parse_value(value):
            """Convierte un valor a float, manejando strings vacíos, None y comas como separador decimal"""
            if value is None or value == '' or value == '0' or value == 0:
                return None
            try:
                # Si es string, limpiar y convertir
                if isinstance(value, str):
                    value = value.strip()
                    if not value or value == '' or value == '0':
                        return None
                    # Reemplazar comas por puntos para formato europeo (ej: "5,6" -> "5.6")
                    # También manejar espacios y otros caracteres
                    value = value.replace(',', '.').replace(' ', '')
                    return float(value)
                # Si ya es numérico, convertir directamente
                return float(value)
            except (ValueError, TypeError) as e:
                logger.debug(f"[MAPPER] No se pudo convertir valor '{value}' (tipo: {type(value)}): {e}")
                return None
        
        # Preparar textura (usar clasificacion de la muestra como en el código original)
        # El código original usa muestras_d["clasificacion"] y lo mapea con texturas_
        codigo_clasificacion = 0
        if muestra:
            # Priorizar clasificacion sobre textura (como en el código original)
            codigo_clasificacion = muestra.get('clasificacion', 0) or muestra.get('textura', 0)
            logger.info(f"[MAPPER] Código de clasificación obtenido de muestra: {codigo_clasificacion}")
        elif textura:
            codigo_clasificacion = textura.get('codigo', 0)
            logger.info(f"[MAPPER] Código de clasificación obtenido de tabla textura: {codigo_clasificacion}")
        
        # Mapeo de código de textura (BD) a valor del formulario (data-value)
        # Basado en inspección real de la BD y valores del formulario
        # BD código -> Nombre BD -> Formulario data-value -> Nombre formulario
        texturas_map = {
            0: "0",   # (vacío) -> "No se solicitó"
            1: "7",   # F.Ar (Franco-Arcillosa) -> "Franco-Arcillosa"
            2: "8",   # F.A. (Franco-Arenosa) -> "Franco-Arenosa"
            3: "1",   # Ar. (Arcillosa) -> "Arcillosa"
            4: "9",   # F.Ar.A (Franco-Arcillo-Arenosa) -> "Franco-Arcillo-Arenosa"
            5: "6",   # F. (Franca) -> "Franca"
            6: "12",  # L (Limosa) -> "Limosa"
            7: "11",  # F.L. (Franco-Limosa) -> "Franco-Limosa"
            8: "10",  # F.Ar.L (Franco-Arcillo-Limosa) -> "Franco-Arcillo-Limosa"
            9: "5",   # A.F. (Arenoso-Franca) -> "Arenoso-Franca"
            10: "4",  # A. (Arenosa) -> "Arenosa"
            11: "3",  # Ar.L. (Arcillo-Limosa) -> "Arcillo-Limosa"
            12: "2",  # Ar.A. (Arcillo-Arenosa) -> "Arcillo-Arenosa"
            13: "11", # F.L. (Franco-Limosa) -> "Franco-Limosa" (duplicado de código 7)
        }
        
        # Convertir código de clasificación (BD) a valor del formulario (data-value)
        codigo_clasificacion_int = int(codigo_clasificacion) if codigo_clasificacion else 0
        
        if codigo_clasificacion_int in texturas_map:
            codigo_textura = texturas_map[codigo_clasificacion_int]
            nombre_bd = f"código {codigo_clasificacion_int}"
            logger.info(f"[MAPPER] Textura BD {codigo_clasificacion_int} → Formulario data-value '{codigo_textura}'")
        else:
            codigo_textura = "0"
            logger.warning(f"[MAPPER] Código de textura {codigo_clasificacion_int} no encontrado en mapeo, usando valor por defecto '0' (No se solicitó)")
        
        # Construir el diccionario de datos para SIASCAFE
        siascafe_data = {
            # Información básica
            'nombre': nombre_solicitante[:50] if nombre_solicitante else '',
            'departamento': nombre_departamento[:26] if nombre_departamento else '',
            'municipio': nombre_municipio[:26] if nombre_municipio else '',
            'codigoMuestra': codigo_muestra[:20] if codigo_muestra else '',
            'codigo': str(orden.get('numero_solicitud', '0'))[:20] if orden else '0',
            'finca': nombre_finca[:26] if nombre_finca else '',
            'lote': referencia[:26] if referencia else '',
            
            # Datos del usuario (tienen prioridad)
            'etapa': user_data.get('etapa', 0),  # 0=Crecimiento, 1=Producción, etc.
            'edad': user_data.get('edad', 0),
            'siembra': user_data.get('densidad', 2000),
            'sombrio': user_data.get('sombrío', 0),
            'fechaMuestreo': fecha_muestreo,
            
            # Valores químicos de la muestra
            'pH': parse_value(muestra.get('ph')) if muestra else None,
            'MO': parse_value(muestra.get('mo')) if muestra else None,
            'P': parse_value(muestra.get('p')) if muestra else None,
            'K': parse_value(muestra.get('k')) if muestra else None,
            'Mg': parse_value(muestra.get('mg')) if muestra else None,
            'Ca': parse_value(muestra.get('ca')) if muestra else None,
            'Al': parse_value(muestra.get('al')) if muestra else None,
            'S': parse_value(muestra.get('s')) if muestra else None,
            'Textura': codigo_textura
        }
        
        # Limpiar valores None (convertirlos a string vacío o 0 según el tipo)
        for key, value in siascafe_data.items():
            if value is None:
                if key in ['pH', 'MO', 'P', 'K', 'Mg', 'Ca', 'Al', 'S']:
                    siascafe_data[key] = ''
                elif key in ['etapa', 'edad', 'siembra', 'sombrio', 'Textura']:
                    siascafe_data[key] = 0
                else:
                    siascafe_data[key] = ''
        
        logger.info("[MAPPER] ✓ Mapeo completado")
        logger.info(f"[MAPPER] Datos finales para SIASCAFE:")
        for key, value in siascafe_data.items():
            logger.info(f"[MAPPER]   - {key}: {value}")
        
        return siascafe_data
    
    @staticmethod
    def validate_user_data(user_data: Dict) -> Dict:
        """
        Valida y normaliza los datos del usuario
        """
        validated = {
            'etapa': int(user_data.get('etapa', 0)),
            'edad': max(0, min(1200, int(user_data.get('edad', 0)))),
            'densidad': max(2000, min(20000, int(user_data.get('densidad', 2000)))),
            'sombrío': max(0, min(100, int(user_data.get('sombrío', 0))))
        }
        
        return validated

