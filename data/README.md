# Directorio de Datos

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
