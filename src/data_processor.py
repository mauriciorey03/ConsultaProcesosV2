#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Procesador de datos para consultas de procesos judiciales
Incluye actuaciones y anotaciones
"""

import logging
from datetime import datetime
from typing import Dict, Any, Tuple, Optional, List
from dataclasses import dataclass

from config import ProcessConfig, UIConfig


logger = logging.getLogger(__name__)


@dataclass
class ProcesoInfo:
    """Clase para almacenar información procesada de un proceso"""
    radicado: str
    demandante: str = ProcessConfig.NO_DATA_PLACEHOLDER
    demandado: str = ProcessConfig.NO_DATA_PLACEHOLDER
    juzgado: str = ProcessConfig.NO_DATA_PLACEHOLDER
    departamento: str = ProcessConfig.NO_DATA_PLACEHOLDER
    tipo_proceso: str = ProcessConfig.NO_DATA_PLACEHOLDER
    clase_proceso: str = ProcessConfig.NO_DATA_PLACEHOLDER
    subclase_proceso: str = ProcessConfig.NO_DATA_PLACEHOLDER
    fecha_ultima_actuacion: str = ProcessConfig.NO_DATA_PLACEHOLDER
    ultima_actuacion: str = ProcessConfig.NO_DATA_PLACEHOLDER  # NUEVO
    anotaciones: str = ProcessConfig.NO_DATA_PLACEHOLDER  # NUEVO
    es_privado: bool = False
    status: str = ProcessConfig.Status.SUCCESS


@dataclass
class EstadisticasProcesamiento:
    """Clase para almacenar estadísticas del procesamiento"""
    total_procesados: int = 0
    exitosos: int = 0
    privados: int = 0
    fallidos: int = 0
    no_encontrados: int = 0
    
    @property
    def tasa_exito(self) -> float:
        """Calcula la tasa de éxito (exitosos + privados / total)"""
        if self.total_procesados == 0:
            return 0.0
        return ((self.exitosos + self.privados) / self.total_procesados) * 100
    
    def incrementar(self, status: str):
        """Incrementa el contador según el status"""
        self.total_procesados += 1
        
        if status == ProcessConfig.Status.SUCCESS:
            self.exitosos += 1
        elif status == ProcessConfig.Status.PRIVATE:
            self.privados += 1
        elif status == ProcessConfig.Status.NOT_FOUND:
            self.no_encontrados += 1
        else:
            self.fallidos += 1


class ProcesosProcessor:
    """Procesador de datos de procesos judiciales"""
    
    def __init__(self):
        """Inicializa el procesador"""
        self.estadisticas = EstadisticasProcesamiento()
        logger.info("Procesador de datos inicializado")
    
    def extraer_sujetos_procesales(self, sujetos_texto: str) -> Tuple[str, str]:
        """
        Extrae demandante y demandado del texto de sujetos procesales
        
        Args:
            sujetos_texto: Texto con la información de sujetos procesales
            
        Returns:
            Tupla con (demandante, demandado)
        """
        demandante = ProcessConfig.NO_DATA_PLACEHOLDER
        demandado = ProcessConfig.NO_DATA_PLACEHOLDER
        
        if not sujetos_texto:
            logger.debug("Texto de sujetos procesales vacío")
            return demandante, demandado
        
        try:
            # Dividir por separador estándar
            partes = sujetos_texto.split(" | ")
            
            for parte in partes:
                parte_limpia = parte.strip()
                
                if "Demandante:" in parte_limpia:
                    demandante = parte_limpia.replace("Demandante:", "").strip()
                    # Limpiar espacios extra y saltos de línea
                    demandante = " ".join(demandante.split())
                    
                elif "Demandado:" in parte_limpia:
                    demandado = parte_limpia.replace("Demandado:", "").strip()
                    # Limpiar espacios extra y saltos de línea
                    demandado = " ".join(demandado.split())
            
            logger.debug(f"Sujetos extraídos - Demandante: {demandante}, Demandado: {demandado}")
            
        except Exception as e:
            logger.error(f"Error al extraer sujetos procesales: {e}")
        
        return demandante, demandado
    
    def extraer_ultima_actuacion(self, actuaciones_data: Dict[str, Any]) -> str:
        """
        Extrae la descripción de la última actuación
        
        Args:
            actuaciones_data: Datos de actuaciones del proceso
            
        Returns:
            Descripción de la última actuación
        """
        if not actuaciones_data:
            return ProcessConfig.NO_DATA_PLACEHOLDER
        
        try:
            actuaciones = actuaciones_data.get('actuaciones', [])
            if actuaciones and len(actuaciones) > 0:
                # Tomar la primera actuación (más reciente)
                ultima = actuaciones[0]
                actuacion = ultima.get('actuacion', '')
                
                if actuacion:
                    # Limpiar y formatear
                    actuacion_limpia = " ".join(actuacion.split())
                    return actuacion_limpia
                    
        except Exception as e:
            logger.error(f"Error al extraer última actuación: {e}")
        
        return ProcessConfig.NO_DATA_PLACEHOLDER
    
    def extraer_anotaciones(self, actuaciones_data: Dict[str, Any]) -> str:
        """
        Extrae las anotaciones de las actuaciones
        
        Args:
            actuaciones_data: Datos de actuaciones del proceso
            
        Returns:
            Anotaciones concatenadas
        """
        if not actuaciones_data:
            return ProcessConfig.NO_DATA_PLACEHOLDER
        
        try:
            actuaciones = actuaciones_data.get('actuaciones', [])
            anotaciones_list = []
            
            for actuacion in actuaciones[:3]:  # Solo las 3 más recientes
                anotacion = actuacion.get('anotacion', '')
                if anotacion and anotacion.strip():
                    anotacion_limpia = " ".join(anotacion.split())
                    anotaciones_list.append(anotacion_limpia)
            
            if anotaciones_list:
                # Unir las anotaciones con separador
                return " | ".join(anotaciones_list)
                
        except Exception as e:
            logger.error(f"Error al extraer anotaciones: {e}")
        
        return ProcessConfig.NO_DATA_PLACEHOLDER
    
    def formatear_fecha(self, fecha_str: str) -> str:
        """
        Formatea una fecha al formato YYYY-MM-DD
        
        Args:
            fecha_str: Fecha en formato ISO o string
            
        Returns:
            Fecha formateada o texto de error
        """
        if not fecha_str:
            return ProcessConfig.NO_DATA_PLACEHOLDER
        
        try:
            # Manejar diferentes formatos de fecha
            if 'T' in fecha_str:
                # Formato ISO con tiempo
                fecha_str = fecha_str.split('T')[0]
            
            # Intentar parsear como ISO date
            fecha = datetime.fromisoformat(fecha_str.replace('Z', ''))
            return fecha.strftime('%Y-%m-%d')
            
        except ValueError:
            try:
                # Intentar otros formatos comunes
                for formato in ['%Y-%m-%d', '%d/%m/%Y', '%Y/%m/%d']:
                    try:
                        fecha = datetime.strptime(fecha_str, formato)
                        return fecha.strftime('%Y-%m-%d')
                    except ValueError:
                        continue
                
                logger.warning(f"No se pudo formatear la fecha: {fecha_str}")
                return fecha_str  # Devolver tal como vino si no se puede formatear
                
            except Exception as e:
                logger.error(f"Error al formatear fecha {fecha_str}: {e}")
                return ProcessConfig.NO_DATA_PLACEHOLDER
    
    def procesar_datos_proceso(self, datos_proceso: Dict[str, Any]) -> ProcesoInfo:
        """
        Procesa los datos brutos de un proceso y los convierte en ProcesoInfo
        
        Args:
            datos_proceso: Diccionario con los datos del proceso
            
        Returns:
            Objeto ProcesoInfo con los datos procesados
        """
        if not datos_proceso:
            logger.error("Datos de proceso vacíos")
            return ProcesoInfo(radicado="UNKNOWN", status=ProcessConfig.Status.FAILED)
        
        radicado = datos_proceso.get('radicado', 'UNKNOWN')
        
        try:
            # Verificar si es proceso privado
            if datos_proceso.get('es_privado', False):
                return self._procesar_proceso_privado(datos_proceso)
            
            # Procesar proceso normal
            return self._procesar_proceso_normal(datos_proceso)
            
        except Exception as e:
            logger.error(f"Error al procesar datos del proceso {radicado}: {e}")
            return ProcesoInfo(radicado=radicado, status=ProcessConfig.Status.FAILED)
    
    def _procesar_proceso_privado(self, datos_proceso: Dict[str, Any]) -> ProcesoInfo:
        """Procesa un proceso privado con información limitada"""
        proceso_basico = datos_proceso.get('proceso_basico', {})
        radicado = datos_proceso.get('radicado', 'UNKNOWN')
        
        # Para procesos privados solo tenemos información básica
        departamento = proceso_basico.get('departamento', ProcessConfig.NO_DATA_PLACEHOLDER)
        juzgado = proceso_basico.get('despacho', ProcessConfig.NO_DATA_PLACEHOLDER).strip()
        fecha_ultima = proceso_basico.get('fechaUltimaActuacion', '')
        fecha_formateada = self.formatear_fecha(fecha_ultima)
        
        logger.info(f"Procesando proceso privado: {radicado}")
        
        return ProcesoInfo(
            radicado=radicado,
            juzgado=juzgado,
            departamento=departamento,
            fecha_ultima_actuacion=fecha_formateada,
            ultima_actuacion="PROCESO PRIVADO - Información restringida",
            anotaciones="PROCESO PRIVADO - Información restringida",
            es_privado=True,
            status=ProcessConfig.Status.PRIVATE
        )
    
    def _procesar_proceso_normal(self, datos_proceso: Dict[str, Any]) -> ProcesoInfo:
        """Procesa un proceso normal con información completa"""
        proceso_basico = datos_proceso.get('proceso_basico', {})
        detalle = datos_proceso.get('detalle', {})
        actuaciones = datos_proceso.get('actuaciones', {})
        radicado = datos_proceso.get('radicado', 'UNKNOWN')
        
        # Extraer sujetos procesales
        sujetos_texto = proceso_basico.get('sujetosProcesales', '')
        demandante, demandado = self.extraer_sujetos_procesales(sujetos_texto)
        
        # Información básica
        departamento = proceso_basico.get('departamento', ProcessConfig.NO_DATA_PLACEHOLDER)
        fecha_ultima = proceso_basico.get('fechaUltimaActuacion', '')
        fecha_formateada = self.formatear_fecha(fecha_ultima)
        
        # Información detallada
        juzgado = detalle.get('despacho', ProcessConfig.NO_DATA_PLACEHOLDER).strip()
        tipo_proceso = detalle.get('tipoProceso', ProcessConfig.NO_DATA_PLACEHOLDER)
        clase_proceso = detalle.get('claseProceso', ProcessConfig.NO_DATA_PLACEHOLDER)
        subclase_proceso = detalle.get('subclaseProceso', ProcessConfig.NO_DATA_PLACEHOLDER)
        
        # Extraer actuaciones y anotaciones (NUEVO)
        ultima_actuacion = self.extraer_ultima_actuacion(actuaciones)
        anotaciones = self.extraer_anotaciones(actuaciones)
        
        logger.debug(f"Procesando proceso normal: {radicado}")
        
        return ProcesoInfo(
            radicado=radicado,
            demandante=demandante,
            demandado=demandado,
            juzgado=juzgado,
            departamento=departamento,
            tipo_proceso=tipo_proceso,
            clase_proceso=clase_proceso,
            subclase_proceso=subclase_proceso,
            fecha_ultima_actuacion=fecha_formateada,
            ultima_actuacion=ultima_actuacion,  # NUEVO
            anotaciones=anotaciones,  # NUEVO
            es_privado=False,
            status=ProcessConfig.Status.SUCCESS
        )
    
    def formatear_resultado_proceso(self, proceso_info: ProcesoInfo) -> str:
        """
        Formatea la información de un proceso para salida
        
        Args:
            proceso_info: Objeto ProcesoInfo con los datos del proceso
            
        Returns:
            String formateado con la información del proceso
        """
        if proceso_info.es_privado:
            return self._formatear_proceso_privado(proceso_info)
        else:
            return self._formatear_proceso_normal(proceso_info)
    
    def _formatear_proceso_privado(self, proceso_info: ProcesoInfo) -> str:
        """Formatea un proceso privado"""
        return f"""{UIConfig.SEPARATOR_RESULT}
Radicado del proceso: {proceso_info.radicado}
{ProcessConfig.PRIVATE_PROCESS_MARKER}
Información disponible:
  Juzgado: {proceso_info.juzgado}
  Departamento: {proceso_info.departamento}
  Última fecha de actuación: {proceso_info.fecha_ultima_actuacion}
  Estado: PROCESO PRIVADO - Información restringida
{UIConfig.SEPARATOR_RESULT}"""
    
    def _formatear_proceso_normal(self, proceso_info: ProcesoInfo) -> str:
        """Formatea un proceso normal"""
        resultado = f"""{UIConfig.SEPARATOR_RESULT}
Radicado del proceso: {proceso_info.radicado}
Información del proceso:
  Demandante: {proceso_info.demandante}
  Demandado: {proceso_info.demandado}
  Juzgado: {proceso_info.juzgado}
  Departamento: {proceso_info.departamento}
  Tipo del proceso: {proceso_info.tipo_proceso}
  Clase del proceso: {proceso_info.clase_proceso}
  Subclase del proceso: {proceso_info.subclase_proceso}
  Última fecha de actuación: {proceso_info.fecha_ultima_actuacion}"""
        
        # Agregar actuación si está disponible
        if proceso_info.ultima_actuacion != ProcessConfig.NO_DATA_PLACEHOLDER:
            resultado += f"\n  Última actuación: {proceso_info.ultima_actuacion}"
        
        # Agregar anotaciones si están disponibles
        if proceso_info.anotaciones != ProcessConfig.NO_DATA_PLACEHOLDER:
            resultado += f"\n  Anotaciones: {proceso_info.anotaciones}"
        
        resultado += f"\n{UIConfig.SEPARATOR_RESULT}"
        
        return resultado
    
    def procesar_lote_procesos(self, lista_datos_procesos: List[Dict[str, Any]]) -> List[ProcesoInfo]:
        """
        Procesa un lote de procesos
        
        Args:
            lista_datos_procesos: Lista de diccionarios con datos de procesos
            
        Returns:
            Lista de objetos ProcesoInfo procesados
        """
        resultados = []
        
        logger.info(f"Procesando lote de {len(lista_datos_procesos)} procesos")
        
        for datos in lista_datos_procesos:
            try:
                proceso_info = self.procesar_datos_proceso(datos)
                resultados.append(proceso_info)
                
                # Actualizar estadísticas
                self.estadisticas.incrementar(proceso_info.status)
                
            except Exception as e:
                radicado = datos.get('radicado', 'UNKNOWN') if datos else 'UNKNOWN'
                logger.error(f"Error al procesar proceso {radicado}: {e}")
                
                # Crear proceso con error
                proceso_error = ProcesoInfo(radicado=radicado, status=ProcessConfig.Status.FAILED)
                resultados.append(proceso_error)
                self.estadisticas.incrementar(ProcessConfig.Status.FAILED)
        
        logger.info(f"Lote procesado: {len(resultados)} procesos")
        return resultados
    
    def generar_reporte_estadisticas(self) -> str:
        """
        Genera un reporte de estadísticas del procesamiento
        
        Returns:
            String con el reporte de estadísticas
        """
        stats = self.estadisticas
        
        reporte = f"""
{UIConfig.SEPARATOR_MAJOR}
RESUMEN DE PROCESAMIENTO
{UIConfig.SEPARATOR_MAJOR}
Total de radicados procesados: {stats.total_procesados}
Consultas exitosas: {stats.exitosos}
Procesos privados: {stats.privados}
Procesos no encontrados: {stats.no_encontrados}
Consultas fallidas: {stats.fallidos}
Tasa de éxito: {stats.tasa_exito:.1f}%
"""
        
        # Agregar detalles adicionales si hay fallos
        if stats.fallidos > 0 or stats.no_encontrados > 0:
            reporte += f"""
{UIConfig.SEPARATOR_MINOR}
DETALLES:
- Procesos exitosos incluyen información completa
- Procesos privados tienen información limitada pero son válidos
- Procesos no encontrados pueden ser radicados incorrectos
- Consultas fallidas incluyen errores de red y otros problemas técnicos
"""
        
        return reporte
    
    def validar_radicado(self, radicado: str) -> Tuple[bool, str]:
        """
        Valida que un radicado tenga el formato correcto
        
        Args:
            radicado: Número de radicación a validar
            
        Returns:
            Tupla con (es_valido, mensaje_error)
        """
        if not radicado or not isinstance(radicado, str):
            return False, "Radicado vacío o no es string"
        
        radicado_limpio = radicado.strip()
        
        if len(radicado_limpio) < ProcessConfig.MIN_RADICADO_LENGTH:
            return False, f"Radicado muy corto (mínimo {ProcessConfig.MIN_RADICADO_LENGTH} caracteres)"
        
        if len(radicado_limpio) > ProcessConfig.MAX_RADICADO_LENGTH:
            return False, f"Radicado muy largo (máximo {ProcessConfig.MAX_RADICADO_LENGTH} caracteres)"
        
        # Verificar que contenga solo números
        if not radicado_limpio.isdigit():
            return False, "Radicado debe contener solo números"
        
        return True, "Válido"
    
    def limpiar_estadisticas(self):
        """Reinicia las estadísticas del procesador"""
        self.estadisticas = EstadisticasProcesamiento()
        logger.info("Estadísticas reiniciadas")
    
    def obtener_resumen_por_departamento(self, procesos: List[ProcesoInfo]) -> Dict[str, int]:
        """
        Genera un resumen de procesos por departamento
        
        Args:
            procesos: Lista de objetos ProcesoInfo
            
        Returns:
            Diccionario con departamento como clave y cantidad como valor
        """
        resumen = {}
        
        for proceso in procesos:
            dep = proceso.departamento
            if dep == ProcessConfig.NO_DATA_PLACEHOLDER:
                dep = "Sin departamento"
            
            resumen[dep] = resumen.get(dep, 0) + 1
        
        # Ordenar por cantidad descendente
        return dict(sorted(resumen.items(), key=lambda x: x[1], reverse=True))
    
    def obtener_resumen_por_tipo(self, procesos: List[ProcesoInfo]) -> Dict[str, int]:
        """
        Genera un resumen de procesos por tipo
        
        Args:
            procesos: Lista de objetos ProcesoInfo
            
        Returns:
            Diccionario con tipo como clave y cantidad como valor
        """
        resumen = {}
        
        for proceso in procesos:
            if proceso.es_privado:
                tipo = "PROCESO PRIVADO"
            else:
                tipo = proceso.tipo_proceso
                if tipo == ProcessConfig.NO_DATA_PLACEHOLDER:
                    tipo = "Sin tipo definido"
            
            resumen[tipo] = resumen.get(tipo, 0) + 1
        
        return dict(sorted(resumen.items(), key=lambda x: x[1], reverse=True))
    
    def generar_reporte_detallado(self, procesos: List[ProcesoInfo]) -> str:
        """
        Genera un reporte detallado con análisis de los procesos
        
        Args:
            procesos: Lista de objetos ProcesoInfo
            
        Returns:
            String con el reporte detallado
        """
        if not procesos:
            return "No hay procesos para generar reporte"
        
        # Resúmenes
        resumen_dept = self.obtener_resumen_por_departamento(procesos)
        resumen_tipo = self.obtener_resumen_por_tipo(procesos)
        
        reporte = f"""
{UIConfig.SEPARATOR_MAJOR}
REPORTE DETALLADO DE PROCESOS
{UIConfig.SEPARATOR_MAJOR}

ANÁLISIS POR DEPARTAMENTO:
"""
        
        for dept, cantidad in resumen_dept.items():
            porcentaje = (cantidad / len(procesos)) * 100
            reporte += f"  {dept}: {cantidad} procesos ({porcentaje:.1f}%)\n"
        
        reporte += f"""
{UIConfig.SEPARATOR_MINOR}
ANÁLISIS POR TIPO DE PROCESO:
"""
        
        for tipo, cantidad in resumen_tipo.items():
            porcentaje = (cantidad / len(procesos)) * 100
            reporte += f"  {tipo}: {cantidad} procesos ({porcentaje:.1f}%)\n"
        
        reporte += f"""
{UIConfig.SEPARATOR_MINOR}
ESTADÍSTICAS GENERALES:
"""
        reporte += self.generar_reporte_estadisticas()
        
        return reporte


class DataValidator:
    """Validador de datos para procesos judiciales"""
    
    @staticmethod
    def validar_datos_proceso(datos: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Valida que los datos de un proceso sean correctos
        
        Args:
            datos: Diccionario con datos del proceso
            
        Returns:
            Tupla con (es_valido, lista_errores)
        """
        errores = []
        
        if not datos:
            errores.append("Datos vacíos")
            return False, errores
        
        # Validar campos requeridos
        campos_requeridos = ['radicado']
        for campo in campos_requeridos:
            if campo not in datos or not datos[campo]:
                errores.append(f"Campo requerido faltante: {campo}")
        
        # Validar estructura para procesos no privados
        if not datos.get('es_privado', False):
            if 'proceso_basico' not in datos:
                errores.append("Falta información básica del proceso")
            
            if 'detalle' not in datos:
                errores.append("Falta información detallada del proceso")
        
        return len(errores) == 0, errores
    
    @staticmethod
    def sanitizar_texto(texto: str) -> str:
        """
        Sanitiza un texto removiendo caracteres problemáticos
        
        Args:
            texto: Texto a sanitizar
            
        Returns:
            Texto sanitizado
        """
        if not texto:
            return ProcessConfig.NO_DATA_PLACEHOLDER
        
        # Remover caracteres de control y espacios extra
        texto_limpio = ' '.join(texto.split())
        
        # Remover caracteres problemáticos
        caracteres_problematicos = ['\x00', '\x01', '\x02', '\x03', '\x04', '\x05']
        for char in caracteres_problematicos:
            texto_limpio = texto_limpio.replace(char, '')
        
        return texto_limpio.strip() if texto_limpio.strip() else ProcessConfig.NO_DATA_PLACEHOLDER