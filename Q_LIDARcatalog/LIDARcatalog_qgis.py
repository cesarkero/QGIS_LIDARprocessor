##LIDAR=group
##LIDARcatalog=name
##LAZfiles=folder

from PyQt4.QtCore import QFileInfo, QSettings, QVariant
from qgis.core import *
import qgis.utils
import os, glob, processing, string

settings = QSettings()
# Take the "CRS for new layers" config, overwrite it while loading layers and...
oldProjValue = settings.value( "/Projections/defaultBehaviour", "prompt", type=str )
settings.setValue( "/Projections/defaultBehaviour", "useProject" )

#crear directorio de salida en funcion del directorio de entrada
Output = str(os.path.dirname(LAZfiles)+"/LAZ_catalog")
if not os.path.exists(Output):
	os.makedirs(Output)

#crear shapefiles de extension de los archivos lidar laz (bounding boxes)
processing.runalg("lidartools:lasboundarypro",LAZfiles,"*.laz",0,2,50,False,False,Output,"",0,"",4,False,False)

#Iterar sobre archivos y crear atributo con el nombre del archivo
lista = list()

print ("Creando atributo directorio en archivos shp")

os.chdir(Output)
for shp in glob.glob("*.shp"):
	directorio = str(Output + '/' + str(shp))
	lista.append(directorio)
	
	# crear campo path para atributos
	path = str(LAZfiles + '/' + str(shp)[:-4] + ".laz")
	
	# manejar datos, crear "Path" y dar nombre de directorio
	layer = QgsVectorLayer(shp, "testlayer_shp", "ogr")
	res = layer.dataProvider()
	res.addAttributes([QgsField("Path", QVariant.String)])
	res.addAttributes([QgsField("File", QVariant.String)])
	attrsPath = {0 : path, 1 : str(str(shp)[:-4] + ".laz")}
	layer.dataProvider().changeAttributeValues({0:attrsPath})
	layer.updateFields()

	# convertir lista en str separado por ;
	lista2 = ';'.join(lista)

print ("Creando LIDAR_catalog")
# merge de todos los shp de la carpeta catalog
processing.runalg("qgis:mergevectorlayers",lista2,str(os.path.dirname(LAZfiles) + '/' + 'LIDAR_catalog.shp'))

settings.setValue( "/Projections/defaultBehaviour", oldProjValue )