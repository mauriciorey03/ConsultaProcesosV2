#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Cliente API para consultas a la Rama Judicial de Colombia
"""

import requests
import json
import time
import logging
from typing import Optional, Dict, Any
from dataclasses import dataclass

try:
    from config import APIConfig, ProcessConfig
except ModuleNotFoundError:
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    from config import APIConfig, ProcessConfig


logger = logging.getLogger(__name__)


@dataclass
class APIResponse:
    """Clase para manejar respuestas de la API"""
    success: bool
    data: Optional[Dict[Any, Any]] = None
    error: Optional[str] = None
    status_code: Optional[int] = None


class RamaJudicialAPIError(Exception):
    """Excepción personalizada para errores de la API"""
    pass


class RamaJudicialClient:
    """Cliente para la API de consulta de procesos de la Rama Judicial"""
    
    def __init__(self):
        """Inicializa el cliente API"""
        self.session = requests.Session()
        self.session.headers.update(APIConfig.HEADERS)
        self.base_url = APIConfig.BASE_URL
        logger.info("Cliente API inicializado")
    
    def _make_request(self, method: str, url: str, **kwargs) -> APIResponse:
        """
        Realiza una petición HTTP con manejo de errores
        
        Args:
            method: Método HTTP (GET, POST, etc.)
            url: URL completa para la petición
            **kwargs: Argumentos adicionales para requests
            
        Returns:
            APIResponse con el resultado de la petición
        """
        try:
            response = self.session.request(
                method=method,
                url=url,
                timeout=APIConfig.REQUEST_TIMEOUT,
                **kwargs
            )
            
            # Manejar códigos de estado específicos
            if response.status_code == 404:
                logger.warning(f"Recurso no encontrado (404): {url}")
                return APIResponse(
                    success=False,
                    error="Recurso no encontrado",
                    status_code=404
                )
            
            elif response.status_code == 500:
                logger.error(f"Error del servidor (500): {url}")
                return APIResponse(
                    success=False,
                    error="Error interno del servidor",
                    status_code=500
                )
            
            elif response.status_code == 429:
                logger.warning(f"Demasiadas peticiones (429): {url}")
                return APIResponse(
                    success=False,
                    error="Demasiadas peticiones - Rate limit alcanzado",
                    status_code=429
                )
            
            # Verificar si la respuesta es exitosa
            response.raise_for_status()
            
            # Intentar parsear JSON
            try:
                data = response.json()
                return APIResponse(success=True, data=data, status_code=response.status_code)
            except json.JSONDecodeError as e:
                logger.error(f"Error al decodificar JSON: {e}")
                return APIResponse(
                    success=False,
                    error=f"Error al decodificar JSON: {e}",
                    status_code=response.status_code
                )
                
        except requests.exceptions.Timeout:
            logger.error(f"Timeout en petición a: {url}")
            return APIResponse(success=False, error="Timeout en la petición")
            
        except requests.exceptions.ConnectionError:
            logger.error(f"Error de conexión a: {url}")
            return APIResponse(success=False, error="Error de conexión")
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error en petición a {url}: {e}")
            return APIResponse(success=False, error=f"Error en petición: {e}")
    
    def consultar_por_radicacion(self, numero_radicacion: str) -> APIResponse:
        """
        Consulta un proceso por número de radicación
        
        Args:
            numero_radicacion: Número de radicación del proceso
            
        Returns:
            APIResponse con los datos del proceso o error
        """
        url = f"{self.base_url}{APIConfig.CONSULTA_RADICACION}"
        params = {
            'numero': numero_radicacion,
            'SoloActivos': 'false',
            'pagina': 1
        }
        
        logger.debug(f"Consultando radicación: {numero_radicacion}")
        response = self._make_request('GET', url, params=params)
        
        if response.success and response.data:
            procesos = response.data.get('procesos', [])
            if procesos:
                logger.info(f"Proceso encontrado para radicación: {numero_radicacion}")
                return APIResponse(success=True, data=procesos[0])
            else:
                logger.warning(f"No se encontraron procesos para: {numero_radicacion}")
                return APIResponse(success=False, error="No se encontraron procesos")
        
        return response
    
    def obtener_detalle_proceso(self, id_proceso: int) -> APIResponse:
        """
        Obtiene los detalles de un proceso por su ID
        
        Args:
            id_proceso: ID del proceso
            
        Returns:
            APIResponse con los detalles del proceso o error
        """
        url = f"{self.base_url}{APIConfig.DETALLE_PROCESO}/{id_proceso}"
        
        logger.debug(f"Obteniendo detalles del proceso ID: {id_proceso}")
        response = self._make_request('GET', url)
        
        if response.success:
            logger.info(f"Detalles obtenidos para proceso ID: {id_proceso}")
        else:
            logger.warning(f"No se pudieron obtener detalles para ID: {id_proceso}")
        
        return response
    
    def obtener_actuaciones_proceso(self, id_proceso: int, pagina: int = 1) -> APIResponse:
        """
        Obtiene las actuaciones de un proceso por su ID
        
        Args:
            id_proceso: ID del proceso
            pagina: Página de resultados (default: 1)
            
        Returns:
            APIResponse con las actuaciones del proceso o error
        """
        url = f"{self.base_url}{APIConfig.ACTUACIONES_PROCESO}/{id_proceso}"
        params = {'pagina': pagina}
        
        logger.debug(f"Obteniendo actuaciones del proceso ID: {id_proceso}")
        response = self._make_request('GET', url, params=params)
        
        if response.success:
            logger.info(f"Actuaciones obtenidas para proceso ID: {id_proceso}")
        else:
            logger.warning(f"No se pudieron obtener actuaciones para ID: {id_proceso}")
        
        return response
    
    def consultar_proceso_completo(self, numero_radicacion: str) -> Dict[str, Any]:
        """
        Realiza una consulta completa de un proceso (radicación + detalles + actuaciones)
        
        Args:
            numero_radicacion: Número de radicación del proceso
            
        Returns:
            Diccionario con toda la información del proceso o None si falla
        """
        logger.info(f"Iniciando consulta completa para: {numero_radicacion}")
        
        # Paso 1: Consultar por radicación
        response_basico = self.consultar_por_radicacion(numero_radicacion)
        if not response_basico.success:
            logger.error(f"Error en consulta básica para {numero_radicacion}: {response_basico.error}")
            return None
        
        proceso_basico = response_basico.data
        
        # Verificar si es proceso privado
        es_privado = proceso_basico.get('esPrivado', False)
        if es_privado:
            logger.info(f"Proceso privado detectado: {numero_radicacion}")
            return {
                'radicado': numero_radicacion,
                'es_privado': True,
                'proceso_basico': proceso_basico,
                'detalle': None,
                'actuaciones': None,
                'status': ProcessConfig.Status.PRIVATE
            }
        
        # Obtener ID del proceso
        id_proceso = proceso_basico.get('idProceso')
        if not id_proceso:
            logger.error(f"No se pudo obtener ID del proceso para: {numero_radicacion}")
            return None
        
        logger.debug(f"ID del proceso obtenido: {id_proceso}")
        
        # Pausa entre requests
        time.sleep(APIConfig.DELAY_BETWEEN_REQUESTS)
        
        # Paso 2: Obtener detalles
        response_detalle = self.obtener_detalle_proceso(id_proceso)
        if not response_detalle.success:
            logger.error(f"Error al obtener detalles para ID {id_proceso}: {response_detalle.error}")
            return None
        
        # Paso 3: Obtener actuaciones (opcional)
        response_actuaciones = self.obtener_actuaciones_proceso(id_proceso)
        actuaciones = response_actuaciones.data if response_actuaciones.success else None
        
        if not response_actuaciones.success:
            logger.warning(f"No se pudieron obtener actuaciones para ID {id_proceso}, continuando...")
        
        resultado = {
            'radicado': numero_radicacion,
            'id_proceso': id_proceso,
            'es_privado': False,
            'proceso_basico': proceso_basico,
            'detalle': response_detalle.data,
            'actuaciones': actuaciones,
            'status': ProcessConfig.Status.SUCCESS
        }
        
        logger.info(f"Consulta completa exitosa para: {numero_radicacion}")
        return resultado
    
    def close(self):
        """Cierra la sesión HTTP"""
        if self.session:
            self.session.close()
            logger.info("Sesión API cerrada")
    
    def __enter__(self):
        """Context manager entry"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close()


class RateLimitedClient(RamaJudicialClient):
    """Cliente con control de rate limiting automático"""
    
    def __init__(self, requests_per_minute: int = 20):
        """
        Args:
            requests_per_minute: Máximo número de requests por minuto
        """
        super().__init__()
        self.requests_per_minute = requests_per_minute
        self.request_times = []
        logger.info(f"Cliente con rate limiting inicializado: {requests_per_minute} requests/min")
    
    def _enforce_rate_limit(self):
        """Enforza el límite de peticiones por minuto"""
        now = time.time()
        
        # Limpiar requests antiguos (más de 1 minuto)
        self.request_times = [t for t in self.request_times if now - t < 60]
        
        # Si hemos alcanzado el límite, esperar
        if len(self.request_times) >= self.requests_per_minute:
            sleep_time = 60 - (now - self.request_times[0])
            if sleep_time > 0:
                logger.info(f"Rate limit alcanzado, esperando {sleep_time:.1f} segundos")
                time.sleep(sleep_time)
                # Limpiar lista después de esperar
                self.request_times = []
        
        # Registrar este request
        self.request_times.append(now)
    
    def _make_request(self, method: str, url: str, **kwargs) -> APIResponse:
        """Override para incluir rate limiting"""
        self._enforce_rate_limit()
        return super()._make_request(method, url, **kwargs)