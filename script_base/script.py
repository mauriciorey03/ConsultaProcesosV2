#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para consultar procesos judiciales de la Rama Judicial de Colombia
Extrae información detallada de procesos por número de radicación
Lee radicados desde archivo Excel
"""

import requests
import json
from datetime import datetime
import time
import pandas as pd
import os

class ConsultorProcesosJudiciales:
    def __init__(self):
        self.base_url = "https://consultaprocesos.ramajudicial.gov.co:448/api/v2"
        self.session = requests.Session()
        # Headers para simular navegador
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'es-ES,es;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
        })
    
    def consultar_por_radicacion(self, numero_radicacion):
        """
        Consulta inicial por número de radicación para obtener el idProceso
        """
        url = f"{self.base_url}/Procesos/Consulta/NumeroRadicacion"
        params = {
            'numero': numero_radicacion,
            'SoloActivos': 'false',
            'pagina': 1
        }
        
        try:
            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            if data.get('procesos') and len(data['procesos']) > 0:
                return data['procesos'][0]
            else:
                print(f"No se encontró información para el radicado: {numero_radicacion}")
                return None
                
        except requests.exceptions.RequestException as e:
            print(f"Error al consultar radicación {numero_radicacion}: {e}")
            return None
        except json.JSONDecodeError as e:
            print(f"Error al decodificar JSON para {numero_radicacion}: {e}")
            return None
    
    def obtener_detalle_proceso(self, id_proceso):
        """
        Obtiene los detalles completos del proceso usando el idProceso
        """
        url = f"{self.base_url}/Proceso/Detalle/{id_proceso}"
        
        try:
            response = self.session.get(url, timeout=30)
            
            if response.status_code == 404:
                print(f"⚠️ Proceso no encontrado (404) para ID: {id_proceso}")
                return None
            elif response.status_code == 500:
                print(f"⚠️ Error del servidor (500) para ID: {id_proceso}")
                return None
            
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            print(f"Error al obtener detalles del proceso {id_proceso}: {e}")
            return None
        except json.JSONDecodeError as e:
            print(f"Error al decodificar JSON de detalles para {id_proceso}: {e}")
            return None
    
    def obtener_actuaciones_proceso(self, id_proceso):
        """
        Obtiene las actuaciones del proceso
        """
        url = f"{self.base_url}/Proceso/Actuaciones/{id_proceso}"
        params = {'pagina': 1}
        
        try:
            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            print(f"Error al obtener actuaciones del proceso {id_proceso}: {e}")
            return None
        except json.JSONDecodeError as e:
            print(f"Error al decodificar JSON de actuaciones para {id_proceso}: {e}")
            return None
    
    def extraer_sujetos_procesales(self, sujetos_texto):
        """
        Extrae demandante y demandado del texto de sujetos procesales
        """
        demandante = "No disponible"
        demandado = "No disponible"
        
        if sujetos_texto:
            partes = sujetos_texto.split(" | ")
            for parte in partes:
                if "Demandante:" in parte:
                    demandante = parte.replace("Demandante:", "").strip()
                elif "Demandado:" in parte:
                    demandado = parte.replace("Demandado:", "").strip()
        
        return demandante, demandado
    
    def formatear_fecha(self, fecha_str):
        """
        Formatea la fecha al formato YYYY-MM-DD
        """
        if not fecha_str:
            return "No disponible"
        
        try:
            # Parsear fecha ISO format
            fecha = datetime.fromisoformat(fecha_str.replace('T', ' ').replace('Z', ''))
            return fecha.strftime('%Y-%m-%d')
        except:
            return fecha_str
    
    def consultar_proceso_completo(self, numero_radicacion):
        """
        Consulta completa de un proceso: información básica, detalles y actuaciones
        """
        # Paso 1: Consultar por radicación para obtener idProceso
        proceso_basico = self.consultar_por_radicacion(numero_radicacion)
        if not proceso_basico:
            return None
        
        # Verificar si el proceso es privado
        es_privado = proceso_basico.get('esPrivado', False)
        if es_privado:
            print(f"🔒 PROCESO PRIVADO DETECTADO")
            print(f"   El proceso {numero_radicacion} está marcado como privado")
            print(f"   No se puede acceder a los detalles del proceso")
            return {
                'radicado': numero_radicacion,
                'es_privado': True,
                'proceso_basico': proceso_basico,
                'detalle': None,
                'actuaciones': None
            }
        
        id_proceso = proceso_basico.get('idProceso')
        if not id_proceso:
            print(f"⚠️ No se pudo obtener ID del proceso para: {numero_radicacion}")
            return None
        
        print(f"✓ ID del proceso encontrado: {id_proceso}")
        
        # Pequeña pausa entre consultas
        time.sleep(1)
        
        # Paso 2: Obtener detalles del proceso
        detalle = self.obtener_detalle_proceso(id_proceso)
        if not detalle:
            print(f"⚠️ No se pudieron obtener detalles para ID: {id_proceso}")
            return None
        
        print(f"✓ Detalles obtenidos correctamente")
        
        # Paso 3: Obtener actuaciones (opcional para fecha de última actuación)
        actuaciones = self.obtener_actuaciones_proceso(id_proceso)
        if actuaciones:
            print(f"✓ Actuaciones obtenidas correctamente")
        else:
            print(f"⚠️ No se pudieron obtener actuaciones, continuando...")
        
        # Combinar toda la información
        resultado = {
            'radicado': numero_radicacion,
            'id_proceso': id_proceso,
            'es_privado': False,
            'proceso_basico': proceso_basico,
            'detalle': detalle,
            'actuaciones': actuaciones
        }
        
        return resultado
    
    def leer_radicados_excel(self, ruta_archivo):
        """
        Lee los radicados desde un archivo Excel
        Busca en la columna A desde la fila 2 hacia abajo
        """
        try:
            if not os.path.exists(ruta_archivo):
                print(f"Error: El archivo no existe: {ruta_archivo}")
                return []
            
            # Leer archivo Excel
            df = pd.read_excel(ruta_archivo, header=None, dtype=str)
            
            # Extraer radicados de la columna A (índice 0) desde la fila 2 (índice 1)
            radicados = []
            
            # Verificar si hay datos en la columna A
            if len(df.columns) > 0:
                # Obtener valores desde la fila 2 (índice 1) hacia abajo
                for i in range(1, len(df)):  # Empezar desde índice 1 (fila 2)
                    valor = df.iloc[i, 0]  # Columna A (índice 0)
                    
                    # Limpiar y validar el valor
                    if pd.notna(valor):
                        radicado = str(valor).strip()
                        if radicado and radicado != '':
                            radicados.append(radicado)
                        else:
                            # Si encuentra una celda vacía, detener la lectura
                            break
                    else:
                        # Si encuentra una celda vacía, detener la lectura
                        break
            
            print(f"Se encontraron {len(radicados)} radicados en el archivo Excel")
            
            # Mostrar los primeros 5 radicados como confirmación
            if radicados:
                print("Primeros radicados encontrados:")
                for i, rad in enumerate(radicados[:5]):
                    print(f"  {i+1}. {rad}")
                if len(radicados) > 5:
                    print(f"  ... y {len(radicados) - 5} más")
            
            return radicados
            
        except Exception as e:
            print(f"Error al leer archivo Excel: {e}")
            return []
    
    def formatear_resultado(self, datos_proceso):
        """
        Formatea el resultado en el formato solicitado
        """
        if not datos_proceso:
            return "No se pudo obtener información del proceso"
        
        radicado = datos_proceso['radicado']
        
        # Verificar si es un proceso privado
        if datos_proceso.get('es_privado', False):
            proceso_basico = datos_proceso['proceso_basico']
            departamento = proceso_basico.get('departamento', 'No disponible')
            despacho = proceso_basico.get('despacho', 'No disponible').strip()
            fecha_ultima = proceso_basico.get('fechaUltimaActuacion', '')
            fecha_formateada = self.formatear_fecha(fecha_ultima)
            
            resultado = f"""--------------------
Radicado del proceso: {radicado}
*** PROCESO PRIVADO ***
Información disponible:
  Juzgado: {despacho}
  Departamento: {departamento}
  Última fecha de actuación: {fecha_formateada}
  Estado: PROCESO PRIVADO - Información restringida
--------------------"""
            return resultado
        
        # Extraer información básica
        proceso_basico = datos_proceso['proceso_basico']
        detalle = datos_proceso['detalle']
        
        # Extraer sujetos procesales
        sujetos_texto = proceso_basico.get('sujetosProcesales', '')
        demandante, demandado = self.extraer_sujetos_procesales(sujetos_texto)
        
        # Información del proceso
        juzgado = detalle.get('despacho', 'No disponible').strip()
        departamento = proceso_basico.get('departamento', 'No disponible')
        tipo_proceso = detalle.get('tipoProceso', 'No disponible')
        clase_proceso = detalle.get('claseProceso', 'No disponible')
        subclase_proceso = detalle.get('subclaseProceso', 'No disponible')
        
        # Fecha de última actuación
        fecha_ultima = proceso_basico.get('fechaUltimaActuacion', '')
        fecha_formateada = self.formatear_fecha(fecha_ultima)
        
        # Formatear salida
        resultado = f"""--------------------
Radicado del proceso: {radicado}
Información del proceso:
  Demandante: {demandante}
  Demandado: {demandado}
  Juzgado: {juzgado}
  Departamento: {departamento}
  Tipo del proceso: {tipo_proceso}
  Clase del proceso: {clase_proceso}
  Subclase del proceso: {subclase_proceso}
  Última fecha de actuación: {fecha_formateada}
--------------------"""
        
        return resultado
        """
        Formatea el resultado en el formato solicitado
        """
        if not datos_proceso:
            return "No se pudo obtener información del proceso"
        
        # Extraer información básica
        proceso_basico = datos_proceso['proceso_basico']
        detalle = datos_proceso['detalle']
        radicado = datos_proceso['radicado']
        
        # Extraer sujetos procesales
        sujetos_texto = proceso_basico.get('sujetosProcesales', '')
        demandante, demandado = self.extraer_sujetos_procesales(sujetos_texto)
        
        # Información del proceso
        juzgado = detalle.get('despacho', 'No disponible').strip()
        departamento = proceso_basico.get('departamento', 'No disponible')
        tipo_proceso = detalle.get('tipoProceso', 'No disponible')
        clase_proceso = detalle.get('claseProceso', 'No disponible')
        subclase_proceso = detalle.get('subclaseProceso', 'No disponible')
        
        # Fecha de última actuación
        fecha_ultima = proceso_basico.get('fechaUltimaActuacion', '')
        fecha_formateada = self.formatear_fecha(fecha_ultima)
        
        # Formatear salida
        resultado = f"""--------------------
Radicado del proceso: {radicado}
Información del proceso:
  Demandante: {demandante}
  Demandado: {demandado}
  Juzgado: {juzgado}
  Departamento: {departamento}
  Tipo del proceso: {tipo_proceso}
  Clase del proceso: {clase_proceso}
  Subclase del proceso: {subclase_proceso}
  Última fecha de actuación: {fecha_formateada}
--------------------"""
        
        return resultado

def main():
    """
    Función principal del script
    """
    # Ruta del archivo Excel
    ruta_excel = r"D:\PROYECTOS\ConsultaV2\data\PROCESOS.xlsx"
    
    # Crear instancia del consultor
    consultor = ConsultorProcesosJudiciales()
    
    print("=== CONSULTA DE PROCESOS JUDICIALES ===")
    print("Rama Judicial de Colombia")
    print("=" * 50)
    
    # Leer radicados desde Excel
    print(f"Leyendo radicados desde: {ruta_excel}")
    radicados = consultor.leer_radicados_excel(ruta_excel)
    
    if not radicados:
        print("No se encontraron radicados para procesar.")
        return
    
    print(f"Iniciando consulta de {len(radicados)} procesos...")
    print("=" * 50)
    
    resultados = []
    procesos_exitosos = 0
    procesos_fallidos = 0
    procesos_privados = 0
    
    for i, radicado in enumerate(radicados, 1):
        try:
            print(f"\n{'='*60}")
            print(f"PROCESANDO {i}/{len(radicados)}: {radicado}")
            print('='*60)
            
            # Consultar proceso completo
            datos = consultor.consultar_proceso_completo(radicado)
            
            if datos:
                # Formatear y mostrar resultado
                resultado_formateado = consultor.formatear_resultado(datos)
                print(resultado_formateado)
                resultados.append(resultado_formateado)
                
                if datos.get('es_privado', False):
                    procesos_privados += 1
                    print(f"🔒 Proceso {i} marcado como PRIVADO")
                else:
                    procesos_exitosos += 1
                    print(f"✅ Proceso {i} completado exitosamente")
            else:
                print(f"❌ No se pudo consultar el proceso: {radicado}")
                procesos_fallidos += 1
            
            # Pausa entre consultas para no sobrecargar el servidor
            if i < len(radicados):  # No hacer pausa después del último
                print(f"⏳ Esperando 3 segundos antes de la siguiente consulta...")
                time.sleep(3)
            
        except KeyboardInterrupt:
            print("\n⚠️ Consulta interrumpida por el usuario")
            break
        except Exception as e:
            print(f"❌ Error inesperado al procesar {radicado}: {e}")
            print(f"   Tipo de error: {type(e).__name__}")
            procesos_fallidos += 1
            continue
    
    # Resumen final
    print("\n" + "=" * 50)
    print("RESUMEN DE CONSULTA")
    print("=" * 50)
    print(f"Total de radicados procesados: {len(radicados)}")
    print(f"Consultas exitosas: {procesos_exitosos}")
    print(f"Procesos privados: {procesos_privados}")
    print(f"Consultas fallidas: {procesos_fallidos}")
    print(f"Tasa de éxito: {((procesos_exitosos + procesos_privados)/len(radicados)*100):.1f}%")
    
    # Opcional: guardar resultados en archivo
    if resultados:
        try:
            nombre_archivo = f'resultados_consulta_procesos_{datetime.now().strftime("%Y%m%d_%H%M%S")}.txt'
            with open(nombre_archivo, 'w', encoding='utf-8') as f:
                f.write("CONSULTA DE PROCESOS JUDICIALES\n")
                f.write(f"Fecha y hora: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"Total de procesos consultados: {procesos_exitosos}\n")
                f.write(f"Procesos privados encontrados: {procesos_privados}\n")
                f.write(f"Procesos fallidos: {procesos_fallidos}\n")
                f.write("=" * 50 + "\n\n")
                for resultado in resultados:
                    f.write(resultado + "\n\n")
            print(f"✅ Resultados guardados en: {nombre_archivo}")
        except Exception as e:
            print(f"❌ Error al guardar archivo: {e}")
    
    print("\nConsulta completada.")

if __name__ == "__main__":
    main()