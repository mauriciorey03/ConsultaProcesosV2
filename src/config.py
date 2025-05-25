#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Configuraciones y constantes para el sistema de consulta de procesos judiciales
"""

import os
import logging
from pathlib import Path
from typing import Dict, Any


class APIConfig:
    """Configuración para la API de la Rama Judicial"""
    
    # URLs de la API
    BASE_URL = "https://consultaprocesos.ramajudicial.gov.co:448/api/v2"
    CONSULTA_RADICACION = "/Procesos/Consulta/NumeroRadicacion"
    DETALLE_PROCESO = "/Proceso/Detalle"
    ACTUACIONES_PROCESO = "/Proceso/Actuaciones"
    
    # Headers HTTP
    HEADERS = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'es-ES,es;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
    }
    
    # Timeouts y delays
    REQUEST_TIMEOUT = 30
    DELAY_BETWEEN_REQUESTS = 1  # segundos
    DELAY_BETWEEN_PROCESSES = 3  # segundos
    
    # Rate limiting
    RATE_LIMIT_REQUESTS_PER_MINUTE = 15
    MAX_RETRIES = 3


class FileConfig:
    """Configuración para manejo de archivos"""
    
    # Rutas del proyecto
    PROJECT_ROOT = Path("D:/PROYECTOS/ConsultaV2")
    
    # Archivos de entrada
    DATA_DIR = PROJECT_ROOT / "data"
    EXCEL_INPUT_FILE = DATA_DIR / "PROCESOS.xlsx"
    EXCEL_COLUMN = 0  # Columna A (índice 0)
    EXCEL_START_ROW = 2  # Empezar desde fila 2
    
    # Archivos de salida
    OUTPUT_DIR = PROJECT_ROOT / "output"
    BACKUP_DIR = PROJECT_ROOT / "backups"
    LOG_DIR = PROJECT_ROOT / "logs"
    
    # Formatos de archivo
    OUTPUT_ENCODING = 'utf-8'
    OUTPUT_DATETIME_FORMAT = "%Y%m%d_%H%M%S"
    
    # Validaciones
    MAX_FILE_SIZE_MB = 50


class ProcessConfig:
    """Configuración para procesamiento de datos"""
    
    # Placeholders para datos faltantes
    NO_DATA_PLACEHOLDER = "No disponible"
    PRIVATE_PROCESS_MARKER = "*** PROCESO PRIVADO ***"
    
    # Validaciones de radicados
    MIN_RADICADO_LENGTH = 15
    MAX_RADICADO_LENGTH = 30
    
    class Status:
        """Estados de procesamiento"""
        SUCCESS = "SUCCESS"
        PRIVATE = "PRIVATE"
        NOT_FOUND = "NOT_FOUND"
        FAILED = "FAILED"


class UIConfig:
    """Configuración para interfaz de usuario"""
    
    # Iconos y símbolos
    CHECK_ICON = "✅"
    ERROR_ICON = "❌"
    WARNING_ICON = "⚠️"
    SUCCESS_ICON = "✓"
    LOADING_ICON = "⏳"
    PRIVATE_ICON = "🔒"
    
    # Separadores
    SEPARATOR_MAJOR = "=" * 60
    SEPARATOR_MINOR = "-" * 40
    SEPARATOR_RESULT = "--------------------"


class LogConfig:
    """Configuración para logging"""
    
    # Niveles de log
    DEFAULT_LEVEL = logging.INFO
    FILE_LEVEL = logging.DEBUG
    CONSOLE_LEVEL = logging.INFO
    
    # Formato de logs
    LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    DATE_FORMAT = '%Y-%m-%d %H:%M:%S'
    
    # Rotación de logs
    MAX_LOG_SIZE_MB = 10
    BACKUP_COUNT = 5


def validate_config():
    """
    Valida que todas las configuraciones sean correctas
    
    Raises:
        ValueError: Si hay problemas en la configuración
    """
    errores = []
    
    # Validar directorios
    try:
        FileConfig.PROJECT_ROOT.mkdir(parents=True, exist_ok=True)
        FileConfig.DATA_DIR.mkdir(parents=True, exist_ok=True)
        FileConfig.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        FileConfig.BACKUP_DIR.mkdir(parents=True, exist_ok=True)
        FileConfig.LOG_DIR.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        errores.append(f"Error creando directorios: {e}")
    
    # Validar archivo Excel
    if not FileConfig.EXCEL_INPUT_FILE.exists():
        errores.append(f"Archivo Excel no encontrado: {FileConfig.EXCEL_INPUT_FILE}")
    
    # Validar URLs
    if not APIConfig.BASE_URL.startswith(('http://', 'https://')):
        errores.append("URL base de API inválida")
    
    # Validar timeouts
    if APIConfig.REQUEST_TIMEOUT <= 0:
        errores.append("Timeout de request debe ser positivo")
    
    if APIConfig.DELAY_BETWEEN_REQUESTS < 0:
        errores.append("Delay entre requests no puede ser negativo")
    
    # Validar configuración de archivos
    if FileConfig.EXCEL_START_ROW < 1:
        errores.append("Fila de inicio de Excel debe ser >= 1")
    
    if ProcessConfig.MIN_RADICADO_LENGTH <= 0:
        errores.append("Longitud mínima de radicado debe ser positiva")
    
    if errores:
        raise ValueError(f"Errores en configuración: {'; '.join(errores)}")


def get_config_summary() -> Dict[str, Any]:
    """
    Obtiene un resumen de la configuración actual
    
    Returns:
        Diccionario con resumen de configuración
    """
    return {
        "api": {
            "base_url": APIConfig.BASE_URL,
            "timeout": APIConfig.REQUEST_TIMEOUT,
            "rate_limit": APIConfig.RATE_LIMIT_REQUESTS_PER_MINUTE
        },
        "archivos": {
            "excel_input": str(FileConfig.EXCEL_INPUT_FILE),
            "output_dir": str(FileConfig.OUTPUT_DIR),
            "encoding": FileConfig.OUTPUT_ENCODING
        },
        "procesamiento": {
            "min_radicado_length": ProcessConfig.MIN_RADICADO_LENGTH,
            "max_radicado_length": ProcessConfig.MAX_RADICADO_LENGTH,
            "delay_between_processes": APIConfig.DELAY_BETWEEN_PROCESSES
        }
    }


def setup_logging(nivel_consola: int = LogConfig.CONSOLE_LEVEL,
                 archivo_log: str = None) -> logging.Logger:
    """
    Configura el sistema de logging
    
    Args:
        nivel_consola: Nivel de logging para consola
        archivo_log: Ruta del archivo de log (opcional)
        
    Returns:
        Logger configurado
    """
    # Configurar logger raíz
    logger = logging.getLogger()
    logger.setLevel(LogConfig.DEFAULT_LEVEL)
    
    # Limpiar handlers existentes
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    # Handler para consola
    console_handler = logging.StreamHandler()
    console_handler.setLevel(nivel_consola)
    console_formatter = logging.Formatter(LogConfig.LOG_FORMAT, LogConfig.DATE_FORMAT)
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)
    
    # Handler para archivo (opcional)
    if archivo_log:
        try:
            file_handler = logging.FileHandler(archivo_log, encoding='utf-8')
            file_handler.setLevel(LogConfig.FILE_LEVEL)
            file_formatter = logging.Formatter(LogConfig.LOG_FORMAT, LogConfig.DATE_FORMAT)
            file_handler.setFormatter(file_formatter)
            logger.addHandler(file_handler)
        except Exception as e:
            logger.warning(f"No se pudo configurar logging a archivo: {e}")
    
    return logger


# Configuración por defecto al importar el módulo
try:
    validate_config()
except ValueError as e:
    print(f"⚠️ Advertencia en configuración: {e}")


# Variables de entorno opcionales
def load_env_config():
    """Carga configuración desde variables de entorno"""
    
    # API Config desde env
    if os.getenv('RAMA_JUDICIAL_API_URL'):
        APIConfig.BASE_URL = os.getenv('RAMA_JUDICIAL_API_URL')
    
    if os.getenv('API_TIMEOUT'):
        try:
            APIConfig.REQUEST_TIMEOUT = int(os.getenv('API_TIMEOUT'))
        except ValueError:
            pass
    
    # File Config desde env
    if os.getenv('EXCEL_INPUT_PATH'):
        FileConfig.EXCEL_INPUT_FILE = Path(os.getenv('EXCEL_INPUT_PATH'))
    
    if os.getenv('OUTPUT_DIR'):
        FileConfig.OUTPUT_DIR = Path(os.getenv('OUTPUT_DIR'))
    
    # Logging desde env
    if os.getenv('LOG_LEVEL'):
        level_map = {
            'DEBUG': logging.DEBUG,
            'INFO': logging.INFO,
            'WARNING': logging.WARNING,
            'ERROR': logging.ERROR
        }
        LogConfig.DEFAULT_LEVEL = level_map.get(os.getenv('LOG_LEVEL').upper(), logging.INFO)


# Cargar configuración de variables de entorno si están disponibles
load_env_config()