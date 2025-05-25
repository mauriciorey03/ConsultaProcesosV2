#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script principal para consulta de procesos judiciales
Rama Judicial de Colombia

Este script orquesta todo el proceso de consulta:
1. Lee radicados desde Excel
2. Consulta la API de la Rama Judicial
3. Procesa y formatea los resultados
4. Genera reportes en múltiples formatos
"""

import sys
import time
import logging
from pathlib import Path
from typing import List

# Agregar src al path para imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Imports locales (ahora desde src/)
try:
    from config import APIConfig, FileConfig, ProcessConfig, UIConfig, validate_config
    from api_client import RamaJudicialClient, RateLimitedClient
    from data_processor import ProcesosProcessor, ProcesoInfo
    from file_manager import FileManager, BackupManager, LogFileManager, verificar_espacio_disco
except ImportError as e:
    print("❌ Error importando módulos:")
    print(f"   {e}")
    print("🔧 Asegúrate de que todos los módulos en src/ estén completos")
    print("📁 Estructura esperada:")
    print("   src/config.py")
    print("   src/api_client.py") 
    print("   src/data_processor.py")
    print("   src/file_manager.py")
    sys.exit(1)

# Configurar logging
logger = logging.getLogger(__name__)


class ConsultaProcesosOrchestrator:
    """Orquestador principal para la consulta de procesos"""
    
    def __init__(self, usar_rate_limiting: bool = True):
        """
        Inicializa el orquestador
        
        Args:
            usar_rate_limiting: Si usar rate limiting automático
        """
        self.usar_rate_limiting = usar_rate_limiting
        self.api_client = None
        self.processor = ProcesosProcessor()
        self.file_manager = FileManager()
        self.backup_manager = BackupManager()
        self.log_manager = LogFileManager()
        
        logger.info("Orquestador inicializado")
    
    def configurar_logging_archivo(self):
        """Configura logging hacia archivo"""
        try:
            file_handler = self.log_manager.configurar_file_handler()
            logging.getLogger().addHandler(file_handler)
            logger.info("Logging hacia archivo configurado")
        except Exception as e:
            logger.warning(f"No se pudo configurar logging hacia archivo: {e}")
    
    def validar_precondiciones(self) -> bool:
        """
        Valida que todas las precondiciones estén cumplidas
        
        Returns:
            True si todas las validaciones pasan
        """
        print(f"{UIConfig.CHECK_ICON} Validando configuración...")
        
        try:
            # Validar configuraciones
            validate_config()
            print(f"{UIConfig.CHECK_ICON} Configuración validada")
            
            # Validar file manager
            es_valido, errores = self.file_manager.validar_configuracion()
            if not es_valido:
                print(f"{UIConfig.ERROR_ICON} Errores en configuración de archivos:")
                for error in errores:
                    print(f"  - {error}")
                return False
            
            print(f"{UIConfig.CHECK_ICON} Archivos validados")
            
            # Verificar espacio en disco
            if not verificar_espacio_disco(FileConfig.OUTPUT_DIR, 50):
                print(f"{UIConfig.WARNING_ICON} Advertencia: Poco espacio en disco")
            
            print(f"{UIConfig.CHECK_ICON} Todas las validaciones pasaron")
            return True
            
        except Exception as e:
            print(f"{UIConfig.ERROR_ICON} Error en validación: {e}")
            logger.error(f"Error en validación de precondiciones: {e}")
            return False
    
    def inicializar_cliente_api(self):
        """Inicializa el cliente API apropiado"""
        if self.usar_rate_limiting:
            self.api_client = RateLimitedClient(requests_per_minute=15)
            print(f"{UIConfig.CHECK_ICON} Cliente API con rate limiting inicializado")
        else:
            self.api_client = RamaJudicialClient()
            print(f"{UIConfig.CHECK_ICON} Cliente API estándar inicializado")
        
        logger.info(f"Cliente API inicializado (rate limiting: {self.usar_rate_limiting})")
    
    def leer_radicados(self) -> List[str]:
        """
        Lee los radicados desde el archivo Excel
        
        Returns:
            Lista de radicados válidos
        """
        try:
            print(f"{UIConfig.LOADING_ICON} Leyendo radicados desde Excel...")
            print(f"   Archivo: {FileConfig.EXCEL_INPUT_FILE}")
            
            radicados = self.file_manager.excel_reader.leer_radicados()
            
            if not radicados:
                print(f"{UIConfig.ERROR_ICON} No se encontraron radicados válidos")
                return []
            
            print(f"{UIConfig.SUCCESS_ICON} {len(radicados)} radicados encontrados")
            
            # Mostrar muestra
            print("\nPrimeros radicados:")
            for i, radicado in enumerate(radicados[:5]):
                print(f"  {i+1}. {radicado}")
            
            if len(radicados) > 5:
                print(f"  ... y {len(radicados) - 5} más")
            
            return radicados
            
        except Exception as e:
            print(f"{UIConfig.ERROR_ICON} Error al leer radicados: {e}")
            logger.error(f"Error al leer radicados: {e}")
            return []
    
    def consultar_procesos(self, radicados: List[str]) -> List[ProcesoInfo]:
        """
        Consulta todos los procesos de la lista
        
        Args:
            radicados: Lista de radicados a consultar
            
        Returns:
            Lista de ProcesoInfo con los resultados
        """
        if not radicados:
            return []
        
        print(f"\n{UIConfig.SEPARATOR_MAJOR}")
        print("INICIANDO CONSULTA DE PROCESOS")
        print(f"{UIConfig.SEPARATOR_MAJOR}")
        
        resultados = []
        
        for i, radicado in enumerate(radicados, 1):
            try:
                print(f"\n{UIConfig.SEPARATOR_MINOR}")
                print(f"PROCESANDO {i}/{len(radicados)}: {radicado}")
                print(f"{UIConfig.SEPARATOR_MINOR}")
                
                # Consulta API
                datos_proceso = self.api_client.consultar_proceso_completo(radicado)
                
                if datos_proceso:
                    # Procesar datos
                    proceso_info = self.processor.procesar_datos_proceso(datos_proceso)
                    resultados.append(proceso_info)
                    
                    # Mostrar resultado formateado
                    resultado_formateado = self.processor.formatear_resultado_proceso(proceso_info)
                    print(resultado_formateado)
                    
                    # Mostrar status
                    if proceso_info.es_privado:
                        print(f"{UIConfig.PRIVATE_ICON} Proceso {i} - PRIVADO")
                    else:
                        print(f"{UIConfig.SUCCESS_ICON} Proceso {i} - COMPLETADO")
                else:
                    print(f"{UIConfig.ERROR_ICON} No se pudo consultar el proceso: {radicado}")
                    
                    # Crear proceso con error
                    proceso_error = ProcesoInfo(radicado=radicado, status=ProcessConfig.Status.FAILED)
                    resultados.append(proceso_error)
                
                # Actualizar estadísticas
                if resultados:
                    self.processor.estadisticas.incrementar(resultados[-1].status)
                
                # Pausa entre consultas
                if i < len(radicados):
                    print(f"{UIConfig.LOADING_ICON} Esperando {APIConfig.DELAY_BETWEEN_PROCESSES} segundos...")
                    time.sleep(APIConfig.DELAY_BETWEEN_PROCESSES)
                
            except KeyboardInterrupt:
                print(f"\n{UIConfig.WARNING_ICON} Consulta interrumpida por el usuario")
                break
                
            except Exception as e:
                print(f"{UIConfig.ERROR_ICON} Error inesperado procesando {radicado}: {e}")
                logger.error(f"Error inesperado procesando {radicado}: {e}")
                
                # Crear proceso con error
                proceso_error = ProcesoInfo(radicado=radicado, status=ProcessConfig.Status.FAILED)
                resultados.append(proceso_error)
                self.processor.estadisticas.incrementar(ProcessConfig.Status.FAILED)
                continue
        
        return resultados
    
    def generar_reportes(self, procesos: List[ProcesoInfo]) -> dict:
        """
        Genera todos los reportes y archivos de salida
        
        Args:
            procesos: Lista de procesos procesados
            
        Returns:
            Diccionario con información de archivos generados
        """
        try:
            print(f"\n{UIConfig.SEPARATOR_MAJOR}")
            print("GENERANDO REPORTES")
            print(f"{UIConfig.SEPARATOR_MAJOR}")
            
            # Procesar archivo completo
            resultado_archivos = self.file_manager.procesar_archivo_completo(
                procesos, self.processor.estadisticas
            )
            
            print(f"\n{UIConfig.SUCCESS_ICON} Archivos generados:")
            for formato, ruta in resultado_archivos["archivos_creados"].items():
                print(f"  - {formato.upper()}: {ruta}")
            
            return resultado_archivos
            
        except Exception as e:
            print(f"{UIConfig.ERROR_ICON} Error al generar reportes: {e}")
            logger.error(f"Error al generar reportes: {e}")
            return {}
    
    def mostrar_resumen_final(self, procesos: List[ProcesoInfo]):
        """
        Muestra el resumen final de la ejecución
        
        Args:
            procesos: Lista de procesos procesados
        """
        print(f"\n{UIConfig.SEPARATOR_MAJOR}")
        print("RESUMEN FINAL")
        print(f"{UIConfig.SEPARATOR_MAJOR}")
        
        # Estadísticas básicas
        stats = self.processor.estadisticas
        print(f"Total de radicados procesados: {stats.total_procesados}")
        print(f"Consultas exitosas: {stats.exitosos}")
        print(f"Procesos privados: {stats.privados}")
        print(f"Procesos no encontrados: {stats.no_encontrados}")
        print(f"Consultas fallidas: {stats.fallidos}")
        print(f"Tasa de éxito: {stats.tasa_exito:.1f}%")
        
        # Análisis adicional
        if procesos:
            resumen_dept = self.processor.obtener_resumen_por_departamento(procesos)
            print(f"\nProcesos por departamento:")
            for dept, cantidad in list(resumen_dept.items())[:5]:  # Top 5
                print(f"  {dept}: {cantidad}")
            
            if len(resumen_dept) > 5:
                print(f"  ... y {len(resumen_dept) - 5} departamentos más")
    
    def ejecutar_consulta_completa(self) -> bool:
        """
        Ejecuta el proceso completo de consulta
        
        Returns:
            True si la ejecución fue exitosa
        """
        try:
            print("=" * 60)
            print("CONSULTA DE PROCESOS JUDICIALES")
            print("Rama Judicial de Colombia")
            print("=" * 60)
            
            # Configurar logging a archivo
            self.configurar_logging_archivo()
            
            # Validar precondiciones
            if not self.validar_precondiciones():
                return False
            
            # Crear backup del archivo Excel
            try:
                print(f"\n{UIConfig.LOADING_ICON} Creando backup del archivo Excel...")
                backup_path = self.backup_manager.crear_backup_excel()
                print(f"{UIConfig.SUCCESS_ICON} Backup creado: {backup_path.name}")
            except Exception as e:
                print(f"{UIConfig.WARNING_ICON} No se pudo crear backup: {e}")
            
            # Inicializar cliente API
            self.inicializar_cliente_api()
            
            # Leer radicados
            radicados = self.leer_radicados()
            if not radicados:
                print(f"{UIConfig.ERROR_ICON} No hay radicados para procesar")
                return False
            
            # Confirmar inicio
            print(f"\n{UIConfig.WARNING_ICON} Se procesarán {len(radicados)} radicados")
            print("Esto puede tomar varios minutos...")
            
            respuesta = input("¿Continuar? (s/N): ").strip().lower()
            if respuesta not in ['s', 'si', 'sí', 'y', 'yes']:
                print("Operación cancelada por el usuario")
                return False
            
            # Consultar procesos
            with self.api_client:  # Context manager para cerrar sesión
                procesos = self.consultar_procesos(radicados)
            
            if not procesos:
                print(f"{UIConfig.ERROR_ICON} No se procesaron procesos")
                return False
            
            # Generar reportes
            self.generar_reportes(procesos)
            
            # Mostrar resumen final
            self.mostrar_resumen_final(procesos)
            
            # Limpiar archivos antiguos
            try:
                backups_eliminados = self.backup_manager.limpiar_backups_antiguos(30)
                logs_eliminados = self.log_manager.limpiar_logs_antiguos(7)
                
                if backups_eliminados > 0 or logs_eliminados > 0:
                    print(f"\n{UIConfig.CHECK_ICON} Limpieza: {backups_eliminados} backups y {logs_eliminados} logs antiguos eliminados")
            except Exception as e:
                logger.warning(f"Error en limpieza de archivos: {e}")
            
            print(f"\n{UIConfig.SUCCESS_ICON} Consulta completada exitosamente")
            return True
            
        except Exception as e:
            print(f"\n{UIConfig.ERROR_ICON} Error fatal en ejecución: {e}")
            logger.error(f"Error fatal en ejecución: {e}")
            return False
        
        finally:
            # Cerrar cliente API si existe
            if self.api_client:
                self.api_client.close()


def mostrar_ayuda():
    """Muestra información de ayuda"""
    print("""
Consulta de Procesos Judiciales - Rama Judicial de Colombia

USO:
    python main.py [opciones]

OPCIONES:
    -h, --help          Mostrar esta ayuda
    --no-rate-limit     Deshabilitar rate limiting automático
    --config-info       Mostrar información de configuración
    --test-config       Solo validar configuración sin ejecutar

ARCHIVOS:
    Entrada: D:/PROYECTOS/ConsultaV2/data/PROCESOS.xlsx
    Salida:  D:/PROYECTOS/ConsultaV2/output/

DESCRIPCIÓN:
    Este script lee radicados desde un archivo Excel y consulta
    la API de la Rama Judicial para obtener información detallada
    de cada proceso.

    Los resultados se guardan en múltiples formatos:
    - TXT: Formato legible para humanos
    - CSV: Para análisis en Excel/hojas de cálculo
    - JSON: Para integración con otros sistemas

EJEMPLOS:
    python main.py                    # Ejecución normal
    python main.py --no-rate-limit    # Sin límite de velocidad
    python main.py --config-info      # Ver configuración
""")


def mostrar_info_configuracion():
    """Muestra información de la configuración actual"""
    try:
        file_manager = FileManager()
        resumen = file_manager.obtener_resumen_configuracion()
        
        print("CONFIGURACIÓN ACTUAL:")
        print("=" * 50)
        
        print(f"\nArchivo Excel:")
        print(f"  Ruta: {resumen['archivo_excel']['ruta']}")
        print(f"  Existe: {resumen['archivo_excel']['existe']}")
        
        if resumen['archivo_excel']['info'].get('error'):
            print(f"  Error: {resumen['archivo_excel']['info']['error']}")
        else:
            info = resumen['archivo_excel']['info']
            print(f"  Filas: {info.get('filas_totales', 'N/A')}")
            print(f"  Tamaño: {info.get('tamaño_bytes', 0)} bytes")
        
        print(f"\nDirectorio de salida:")
        print(f"  Ruta: {resumen['directorio_salida']['ruta']}")
        print(f"  Existe: {resumen['directorio_salida']['existe']}")
        print(f"  Archivos existentes: {resumen['directorio_salida']['archivos_existentes']}")
        
        print(f"\nConfiguración:")
        print(f"  Columna Excel: {resumen['configuracion']['columna_excel']}")
        print(f"  Fila inicio: {resumen['configuracion']['fila_inicio']}")
        print(f"  Encoding salida: {resumen['configuracion']['encoding_salida']}")
        
    except Exception as e:
        print(f"❌ Error mostrando configuración: {e}")
        print("🔧 Asegúrate de completar todos los módulos en src/")


def main():
    """Función principal"""
    
    # Procesar argumentos de línea de comandos
    import sys
    
    if len(sys.argv) > 1:
        arg = sys.argv[1]
        
        if arg in ['-h', '--help']:
            mostrar_ayuda()
            return 0
        
        elif arg == '--config-info':
            mostrar_info_configuracion()
            return 0
        
        elif arg == '--test-config':
            print("Validando configuración...")
            try:
                validate_config()
                file_manager = FileManager()
                es_valido, errores = file_manager.validar_configuracion()
                
                if es_valido:
                    print(f"✅ Configuración válida")
                    return 0
                else:
                    print(f"❌ Errores en configuración:")
                    for error in errores:
                        print(f"  - {error}")
                    return 1
                    
            except Exception as e:
                print(f"❌ Error en validación: {e}")
                return 1
    
    # Determinar opciones
    usar_rate_limiting = '--no-rate-limit' not in sys.argv
    
    # Ejecutar consulta
    try:
        orquestador = ConsultaProcesosOrchestrator(usar_rate_limiting=usar_rate_limiting)
        exito = orquestador.ejecutar_consulta_completa()
        return 0 if exito else 1
        
    except KeyboardInterrupt:
        print(f"\n{UIConfig.WARNING_ICON} Proceso interrumpido por el usuario")
        return 1
        
    except Exception as e:
        print(f"\n{UIConfig.ERROR_ICON} Error fatal: {e}")
        logger.error(f"Error fatal en main: {e}")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)