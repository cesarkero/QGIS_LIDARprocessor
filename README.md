# Q_LIDARprocessor

# Objetivo:
Herramienta de análisis de datos LIDAR en formato .LAZ descargados de CNIG. Solo se utilizan herramientas FUSION y las propias de QGIS 2.18.12.
Los resultados de la herramienta son: 
-- MDT
-- MDE
-- MDE hillshade
-- MDE normalizado

# Requisitos técnicos: 
- QGIS 2.18.12
- FUSION 3.70 (recordar copiar dentro de C:/FUSION el archivo LAZzip.ddl de la carpeta de lastools)
- Lastools (201804)

# Parámetros:
- Capa shapefile de polygono del buffer del área de influencia del proyecto.
- Capa shapefile de catálogo de archivos LIDAR (con attributos "Path" y "File") --> Se crea con la herramienta LIDARcatalog).
- Directorio de salida donde se guardarán los resultados del proceso.

# Descripción del proceso: 
1. Selección de teselas de la capa catalog a partir de la capa buffer.
2. Filtrado de archivos .laz en caso de que haya repetidos y creación de lista de directorios para introducir en FUSION.
3. En caso de que la lista de directorios (Paths) sean muy grande --> merge de archivos para procesar archivo único.
4. Creación de MDE a partir de la herramienta CANOPY MODEL (FUSION).
5. Creación de hillshade del MDE (como ayuda a la visualización en relieve).
6. Creación del MDT a partir de la herramienta TIN SURFACE (solo seleccionando la clase de datos 2-ground)
7. Creación del MDE normalizado (MDE-MDT) para visualizar alturas de objetos y vegetación.