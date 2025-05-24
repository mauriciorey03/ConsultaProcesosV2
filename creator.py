#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Creator Script - Generador de estructura del proyecto
Consulta de Procesos Judiciales - Rama Judicial Colombia

Este script crea automáticamente toda la estructura de directorios
y archivos base para el proyecto modularizado.
"""

import os
from pathlib import Path
from datetime import datetime


class ProjectCreator:
    """Creador de estructura del proyecto"""
    
    def __init__(self, base_path: str = None):
        """
        Inicializa el creador con la ruta base del proyecto
        
        Args:
            base_path: Ruta base donde crear el proyecto (default: D:/PROYECTOS/ConsultaV2)
        """
        self.base_path = Path(base_path) if base_path else Path("D:/PROYECTOS/ConsultaV2")
        self.created_files = []
        self.created_dirs = []
    
    def create_directory_structure(self):
        """Crea la estructura de directorios del proyecto"""
        directories = [
            self.base_path,
            self.base_path / "src",
            self.base_path / "data", 
            self.base_path / "output",
            self.base_path / "backups",
            self.base_path / "logs",
            self.base_path / "tests",  # Para futuros tests
        ]
        
        print("🏗️  Creando estructura de directorios...")
        
        for directory in directories:
            try:
                directory.mkdir(parents=True, exist_ok=True)
                self.created_dirs.append(str(directory))
                print(f"   ✅ {directory}")
            except Exception as e:
                print(f"   ❌ Error creando {directory}: {e}")
    
    def create_file_templates(self):
        """Crea todos los archivos base con plantillas"""
        
        files_to_create = [
            # Archivos principales
            ("main.py", self.get_main_template()),
            ("requirements.txt", self.get_requirements_template()),
            ("README.md", self.get_readme_template()),
            (".gitignore", self.get_gitignore_template()),
            
            # Módulos src/
            ("src/__init__.py", self.get_src_init_template()),
            ("src/config.py", self.get_config_template()),
            ("src/api_client.py", self.get_api_client_template()),
            ("src/data_processor.py", self.get_data_processor_template()),
            ("src/file_manager.py", self.get_file_manager_template()),
            
            # Archivos de configuración y documentación adicional
            ("config.example.ini", self.get_config_ini_template()),
            ("CHANGELOG.md", self.get_changelog_template()),
            ("data/README.md", self.get_data_readme_template()),
            
            # Archivos de test (estructura básica)
            ("tests/__init__.py", "# Tests module\n"),
            ("tests/test_api_client.py", self.get_test_template("api_client")),
            ("tests/test_data_processor.py", self.get_test_template("data_processor")),
            ("tests/test_file_manager.py", self.get_test_template("file_manager")),
        ]
        
        print("\n📄 Creando archivos base...")
        
        for filename, content in files_to_create:
            self.create_file(filename, content)
    
    def create_file(self, filename: str, content: str):
        """
        Crea un archivo individual con el contenido especificado
        
        Args:
            filename: Nombre del archivo relativo a base_path
            content: Contenido del archivo
        """
        file_path = self.base_path / filename
        
        try:
            # Crear directorio padre si no existe
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Escribir archivo
            file_path.write_text(content, encoding='utf-8')
            self.created_files.append(str(file_path))
            print(f"   ✅ {filename}")
            
        except Exception as e:
            print(f"   ❌ Error creando {filename}: {e}")
    
    def create_sample_excel(self):
        """Crea un archivo Excel de ejemplo con algunos radicados"""
        try:
            import pandas as pd
            
            # Datos de ejemplo
            data = {
                'rad': [
                    '68001310300420200015000',
                    '13160408900120240000600', 
                    '68001333301520240007300',
                    '13670408900120250002800',
                    '13670408900120240030800'
                ]
            }
            
            df = pd.DataFrame(data)
            excel_path = self.base_path / "data" / "PROCESOS.xlsx"
            
            df.to_excel(excel_path, index=False)
            self.created_files.append(str(excel_path))
            print(f"   ✅ data/PROCESOS.xlsx (archivo de ejemplo)")
            
        except ImportError:
            print("   ⚠️  pandas no disponible, creando archivo Excel manualmente...")
            # Crear archivo CSV como alternativa
            csv_content = "rad\n68001310300420200015000\n13160408900120240000600\n68001333301520240007300\n"
            self.create_file("data/PROCESOS_EJEMPLO.csv", csv_content)
            print("   ✅ data/PROCESOS_EJEMPLO.csv (convertir a Excel manualmente)")
            
        except Exception as e:
            print(f"   ❌ Error creando Excel de ejemplo: {e}")
    
    def generate_project(self):
        """Genera todo el proyecto completo"""
        print("🚀 GENERADOR DE PROYECTO - CONSULTA PROCESOS JUDICIALES")
        print("=" * 60)
        print(f"📁 Ruta del proyecto: {self.base_path}")
        print()
        
        # Crear estructura
        self.create_directory_structure()
        self.create_file_templates()
        self.create_sample_excel()
        
        # Mostrar resumen
        self.show_summary()
        
        # Mostrar siguientes pasos
        self.show_next_steps()
    
    def show_summary(self):
        """Muestra un resumen de lo creado"""
        print(f"\n📊 RESUMEN DE CREACIÓN")
        print("=" * 40)
        print(f"Directorios creados: {len(self.created_dirs)}")
        print(f"Archivos creados: {len(self.created_files)}")
        print()
        
        print("📁 Estructura del proyecto:")
        for directory in sorted(self.created_dirs):
            rel_path = Path(directory).relative_to(self.base_path.parent)
            print(f"   {rel_path}/")
        
        print()
        print("📄 Archivos principales:")
        main_files = [f for f in self.created_files if not "/tests/" in f and not "/__pycache__/" in f]
        for file_path in sorted(main_files)[:15]:  # Mostrar primeros 15
            rel_path = Path(file_path).relative_to(self.base_path)
            print(f"   {rel_path}")
        
        if len(main_files) > 15:
            print(f"   ... y {len(main_files) - 15} archivos más")
    
    def show_next_steps(self):
        """Muestra los siguientes pasos para completar el proyecto"""
        print(f"\n🎯 SIGUIENTES PASOS")
        print("=" * 40)
        print("1. 📝 Completar el código en los archivos creados:")
        print("   - src/config.py")
        print("   - src/api_client.py") 
        print("   - src/data_processor.py")
        print("   - src/file_manager.py")
        print("   - main.py")
        print()
        print("2. 📦 Instalar dependencias:")
        print("   cd", str(self.base_path))
        print("   pip install -r requirements.txt")
        print()
        print("3. 📋 Configurar archivo Excel:")
        print("   - Editar data/PROCESOS.xlsx con tus radicados")
        print("   - Formato: Columna A, desde fila 2")
        print()
        print("4. 🚀 Ejecutar el proyecto:")
        print("   python main.py")
        print()
        print("5. 🔧 Configuración avanzada (opcional):")
        print("   - Editar config.example.ini y renombrar a config.ini")
        print("   - Ajustar rutas en src/config.py si es necesario")
        print()
        print("✨ ¡Proyecto base creado exitosamente!")
    
    # =====================================================================
    # PLANTILLAS DE ARCHIVOS
    # =====================================================================
    
    def get_main_template(self):
        """Plantilla para main.py"""
        return '''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script principal para consulta de procesos judiciales
Rama Judicial de Colombia

Autor: Tu Nombre
Fecha: ''' + datetime.now().strftime("%Y-%m-%d") + '''
"""

# TODO: Completar con el código del main.py modularizado

if __name__ == "__main__":
    print("🏛️ Consulta de Procesos Judiciales - Rama Judicial Colombia")
    print("⚠️  Completar implementación en main.py")
'''
    
    def get_requirements_template(self):
        """Plantilla para requirements.txt"""
        return '''# Dependencias para Consulta de Procesos Judiciales
# Rama Judicial de Colombia

# HTTP requests
requests>=2.31.0

# Manejo de archivos Excel
pandas>=2.0.0
openpyxl>=3.1.0

# Utilidades adicionales
colorama>=0.4.6
tqdm>=4.65.0

# Para testing (desarrollo)
pytest>=7.0.0
pytest-cov>=4.0.0
'''
    
    def get_src_init_template(self):
        """Plantilla para src/__init__.py"""
        return '''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Módulo de consulta de procesos judiciales
Rama Judicial de Colombia
"""

__version__ = "1.0.0"
__author__ = "Tu Nombre"
__description__ = "Sistema modular para consulta de procesos judiciales en Colombia"

# TODO: Completar imports cuando los módulos estén implementados
# from .config import APIConfig, FileConfig, ProcessConfig, UIConfig
# from .api_client import RamaJudicialClient, RateLimitedClient
# from .data_processor import ProcesosProcessor, ProcesoInfo
# from .file_manager import FileManager, ExcelReader, ResultWriter
'''
    
    def get_config_template(self):
        """Plantilla para src/config.py"""
        return '''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Configuraciones y constantes para el sistema de consulta de procesos judiciales
"""

# TODO: Completar con todas las configuraciones del módulo config.py
# Incluir:
# - APIConfig
# - FileConfig  
# - ProcessConfig
# - UIConfig
# - LogConfig
# - Funciones de validación

print("⚠️ config.py - Completar implementación")
'''
    
    def get_api_client_template(self):
        """Plantilla para src/api_client.py"""
        return '''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Cliente API para consultas a la Rama Judicial de Colombia
"""

# TODO: Completar con el código del módulo api_client.py
# Incluir:
# - RamaJudicialClient
# - RateLimitedClient  
# - APIResponse
# - Manejo de errores

print("⚠️ api_client.py - Completar implementación")
'''
    
    def get_data_processor_template(self):
        """Plantilla para src/data_processor.py"""
        return '''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Procesador de datos para consultas de procesos judiciales
"""

# TODO: Completar con el código del módulo data_processor.py
# Incluir:
# - ProcesosProcessor
# - ProcesoInfo
# - EstadisticasProcesamiento
# - DataValidator

print("⚠️ data_processor.py - Completar implementación")
'''
    
    def get_file_manager_template(self):
        """Plantilla para src/file_manager.py"""
        return '''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gestor de archivos para el sistema de consulta de procesos judiciales
"""

# TODO: Completar con el código del módulo file_manager.py
# Incluir:
# - ExcelReader
# - ResultWriter
# - FileManager
# - BackupManager

print("⚠️ file_manager.py - Completar implementación")
'''
    
    def get_readme_template(self):
        """Plantilla para README.md"""
        return '''# 🏛️ Consulta de Procesos Judiciales - Rama Judicial Colombia

Sistema modular para consultar procesos judiciales desde la API oficial de la Rama Judicial de Colombia.

## 🚀 Estado del Proyecto

⚠️ **PROYECTO EN DESARROLLO** - Completar implementación de módulos

## 📋 Características Planificadas

- ✅ Estructura modular creada
- ⏳ Lectura automática desde archivos Excel
- ⏳ Rate limiting automático para proteger la API
- ⏳ Manejo de procesos privados
- ⏳ Múltiples formatos de salida (TXT, CSV, JSON)

## 🛠️ Instalación

```bash
pip install -r requirements.txt
```

## 📁 Estructura del Proyecto

```
ConsultaV2/
├── src/                      # Módulos principales
│   ├── config.py            # ⏳ Configuraciones
│   ├── api_client.py        # ⏳ Cliente API
│   ├── data_processor.py    # ⏳ Procesamiento
│   └── file_manager.py      # ⏳ Gestión de archivos
├── data/                    # Archivos de entrada
├── output/                  # Resultados
├── main.py                  # ⏳ Script principal
└── requirements.txt         # ✅ Dependencias
```

## 🎯 Siguientes Pasos

1. Completar implementación de módulos en `src/`
2. Configurar archivo Excel con radicados
3. Probar funcionalidad básica
4. Agregar tests y documentación

---

⚖️ Rama Judicial de Colombia - v1.0.0 (En desarrollo)
'''
    
    def get_gitignore_template(self):
        """Plantilla para .gitignore"""
        return '''# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg
MANIFEST

# Virtual environments
.env
.venv
env/
venv/
ENV/
env.bak/
venv.bak/

# IDEs
.vscode/
.idea/
*.swp
*.swo
*~

# Logs
logs/
*.log

# Output files
output/
backups/

# Configuración local
config.ini

# Data files (opcional, comentar si quieres versionar)
# data/*.xlsx
# data/*.csv

# OS
.DS_Store
Thumbs.db

# Test coverage
htmlcov/
.coverage
.coverage.*
coverage.xml
*.cover
.hypothesis/
.pytest_cache/
'''
    
    def get_config_ini_template(self):
        """Plantilla para config.example.ini"""
        return '''# Archivo de configuración ejemplo
# Copiar a config.ini y personalizar

[API]
base_url = https://consultaprocesos.ramajudicial.gov.co:448/api/v2
timeout = 30
rate_limit_requests_per_minute = 15

[FILES]
excel_input = data/PROCESOS.xlsx
output_directory = output
backup_directory = backups

[PROCESSING]
max_retries = 3
delay_between_requests = 1
delay_between_processes = 3

[LOGGING]
level = INFO
file_logging = true
log_directory = logs
'''
    
    def get_changelog_template(self):
        """Plantilla para CHANGELOG.md"""
        return f'''# Changelog

## [1.0.0] - {datetime.now().strftime("%Y-%m-%d")}

### Agregado
- ✅ Estructura base del proyecto creada
- ✅ Plantillas de módulos generadas
- ✅ Configuración de dependencias
- ✅ Documentación básica

### Por hacer
- ⏳ Implementar módulo config.py
- ⏳ Implementar módulo api_client.py
- ⏳ Implementar módulo data_processor.py
- ⏳ Implementar módulo file_manager.py
- ⏳ Implementar script principal main.py
- ⏳ Agregar tests unitarios
- ⏳ Optimizar rendimiento
'''
    
    def get_data_readme_template(self):
        """Plantilla para data/README.md"""
        return '''# Directorio de Datos

Este directorio contiene los archivos de entrada para el sistema.

## Archivos

### PROCESOS.xlsx
Archivo principal con los radicados a consultar.

**Formato requerido:**
- Columna A: radicados
- Fila 1: header ("rad" o similar)  
- Datos desde fila 2

**Ejemplo:**
```
A          | B | C
rad        |   |
68001310300420200015000 |   |
13160408900120240000600 |   |
68001333301520240007300 |   |
```

## Notas
- El archivo debe estar en formato Excel (.xlsx)
- Los radicados deben ser números válidos
- Celdas vacías detienen la lectura automáticamente
'''
    
    def get_test_template(self, module_name):
        """Plantilla genérica para archivos de test"""
        return f'''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tests para el módulo {module_name}
"""

import pytest
import sys
from pathlib import Path

# Agregar src al path para imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

# TODO: Completar tests para {module_name}

def test_{module_name}_example():
    """Test de ejemplo"""
    assert True, "Test de ejemplo - completar implementación"

# TODO: Agregar más tests específicos
'''


def main():
    """Función principal del creator"""
    print("🏗️ CREATOR - Generador de Proyecto Modular")
    print("Consulta de Procesos Judiciales - Rama Judicial Colombia")
    print("=" * 60)
    
    # Obtener ruta personalizada si se desea
    ruta_personalizada = input("📁 Ruta del proyecto (Enter para D:/PROYECTOS/ConsultaV2): ").strip()
    
    if ruta_personalizada:
        base_path = ruta_personalizada
    else:
        base_path = "D:/PROYECTOS/ConsultaV2"
    
    # Verificar si ya existe
    if Path(base_path).exists():
        respuesta = input(f"⚠️  El directorio {base_path} ya existe. ¿Continuar? (s/N): ").strip().lower()
        if respuesta not in ['s', 'si', 'sí', 'y', 'yes']:
            print("❌ Operación cancelada")
            return
    
    # Crear proyecto
    creator = ProjectCreator(base_path)
    creator.generate_project()


if __name__ == "__main__":
    main()