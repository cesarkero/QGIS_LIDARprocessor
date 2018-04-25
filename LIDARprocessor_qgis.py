##LIDAR=group
##LIDARprocessor=name
##Buffer=vector
##Catalog=vector
##Output=folder
##MDT=boolean TRUE
##MDE=boolean TRUE
##MDEhs=boolean TRUE
##MDEnorm=boolean TRUE
##Resolucion=number 1

from PyQt4.QtCore import QFileInfo, QSettings, QVariant
from qgis.core import *
import qgis.utils
import os, glob, processing, string, time, shutil

#PROCESO PARA ZONAS GRANDES CON VARIOS LAZ INICIALES
#Todo empieza con la copia de los archivos laz necesarios a un unico directorio (temporal)

#seleccionar entidades del shp LIDAR_catalogo (debe estar cargado en canvas y con el mismo nombre LIDAR_catalog)
print ("Recorte de catalogo con buffer")
recorte= str(Output+"/"+"lidar.shp")
processing.runalg("saga:polygonclipping",Buffer,Catalog,recorte)

#proceso de creacion de una lista de paths de archivos SIN REPETIDOS
print ("Creando lista de archivos .laz unicos")
paths = list()
files = list()
layer = processing.getObject(recorte)
layersel = layer.getFeatures()

for feat in layersel:
	geom=feat.geometry()
	paths.append(feat.attributes()[0])
	files.append(feat.attributes()[1])

Filecheck = list()
Pathlist = list()
count=0
#crear lista de valores unicos y append path (Pathlist sera la lista de archivos laz a procesar)
for f in files:
	if f not in Filecheck:
		Filecheck.append(f)
		Pathlist.append(paths[count])
	count+=1

Pathlist2 = ';'.join(Pathlist)

#________________________________________________________________________________________________________
#si la longitud de la lista string es mayor a 1500 caracteres habra que juntar los arhivos laz antes de procesar
if len(Pathlist2)<1500:
	print ("Ejecutando proceso sencillo para pocos archivos LAZ")
	#MDE -- usar FUSION canopy model a 1m y crear asc y dtm
	MDEdtm = str(Output+"/"+"MDE.dtm")
	MDEasc = str(Output+"/"+"MDE.asc")
	MDEtif = str(Output+"/"+"MDE.tif")
	MDEmar = str(Output+'/'+"MDEmar.asc")
	MDEmartif = str(Output+'/'+"MDEmar.tif")
	MDTdtm = str(Output+"/"+"MDT.dtm")
	MDTtif = str(Output+"/"+"MDT.tif")
	MDEn = str(Output+"/"+"MDEnorm.tif")
	MDE_hs = str(Output+"/"+"MDE_hs.tif")

	if MDE == True:
		print ("Creando MDE")
		processing.runalg("lidartools:canopymodel",Pathlist2,Resolucion,0,0,"","","","",False,True,"",MDEdtm)
		time.sleep(5)
		# convertir asc en tif y extension del raster (servira para los procesos posteriores)
		rasterlayer = QgsRasterLayer(MDEasc,"rasterlayer")
		rasterext = rasterlayer.extent()
		xmin = rasterext.xMinimum()
		xmax = rasterext.xMaximum()
		ymin = rasterext.yMinimum()
		ymax = rasterext.yMaximum()
		extension = "%f,%f,%f,%f" %(xmin, xmax, ymin, ymax)
		processing.runalg("gdalogr:translate",MDEasc,100,True,"",0,"EPSG:25829",extension,False,5,4,75,6,1,False,0,False,"",MDEtif)
		# cambiar null por 0
		processing.runalg("saga:reclassifygridvalues",MDEasc,0,0,1,0,0,1,2,0,"0,0,0,0,0,0,0,0,0",0,True,0,False,0,MDEmar)
		processing.runalg("gdalogr:translate",MDEmar,100,True,"",0,"EPSG:25829",extension,False,5,4,75,6,1,False,0,False,"",MDEmartif)

	#MDEhs para sombreado de alturas
	if MDEhs == True:
		print ("Creando MDE_hs")
		processing.runalg("gdalogr:hillshade",MDEtif,1,False,False,1,1,315,45,MDE_hs)

	#MDT -- usar FUSION crear superficie TIN seleccionando solo la clase 2 (ground)
	if MDT == True:
		print ("Creando MDT")
		processing.runalg("lidartools:tinsurfacecreate",Pathlist2,Resolucion,0,0,"2","",MDTdtm)
		processing.runalg("gdalogr:translate",MDTdtm,100,True,"",0,"EPSG:25829",extension,False,5,4,75,6,1,False,0,False,"",MDTtif)

	#MDEnorm -- MDE - MDT con GDAL rastercalculator
	if MDEnorm == True:
		print ("Creando MDEnorm")
		processing.runalg("saga:rastercalculator",MDEmartif,MDTtif,"a-b",3,False,7,MDEn)
#________________________________________________________________________________________________________

else:
	print ("Ejecutando algoritmo largo con lastile")
	# crear path de LAZ_files y copiar files y crear LAZ_tile
	LAZ_files = str(Output+'/'+'_01_LAZ_files/')
	LAZ_tile = Output+'/'+'_02_LAZ_tile/'
	LAZ_MDE = str(Output+'/'+'_03_LAZ_MDE')
	LAZ_MDEtif = str(Output+'/'+'_04_LAZ_MDEtif')
	LAZ_MDEmar = str(Output+'/'+'_05_LAZ_MDEmar')
	LAZ_MDEmartif = str(Output+'/'+'_06_LAZ_MDEmartif')
	LAZ_MDT = str(Output+'/'+'_07_LAZ_MDT')
	LAZ_MDTtif = str(Output+'/'+'_08_LAZ_MDTtif')
	
	try:
		os.makedirs(LAZ_files)
		os.makedirs(LAZ_tile)
		os.makedirs(LAZ_MDE)
		os.makedirs(LAZ_MDEtif)
		os.makedirs(LAZ_MDEmar)
		os.makedirs(LAZ_MDEmartif)
		os.makedirs(LAZ_MDT)
		os.makedirs(LAZ_MDTtif)
	except OSError:
		pass
		
	# LASTILEPRO con 2000m entre tiles y buffer 25m (antes copiar archivos laz a procesar)
	if os.path.isdir(LAZ_files):
		for p in Pathlist:
			shutil.copy2(p, LAZ_files)
	processing.runalg("lidartools:lastilepro",LAZ_files,"*.laz",False,False,5000,25,True,False,LAZ_tile,"LAZ.laz",0,"",False,False)
	
	for laz in os.listdir(LAZ_tile):
		lazfile = str(laz)
		lazdir = str(LAZ_tile+'/'+lazfile)
		
		# MDE -- usar FUSION canopy model a 1m y crear asc y dtm
		MDEdtm = str(LAZ_MDE+"/"+laz[0:-4]+"_MDE.dtm")
		MDEasc = str(LAZ_MDE+"/"+laz[0:-4]+"_MDE.asc")
		MDEtif = str(LAZ_MDEtif+"/"+laz[0:-4]+"_MDE.tif")
		MDEmar = str(LAZ_MDEmar+'/'+laz[0:-4]+"_MDEmar.asc")
		MDEmartif = str(LAZ_MDEmartif+'/'+laz[0:-4]+"_MDEmar.tif")
		MDTdtm = str(LAZ_MDT+"/"+laz[0:-4]+"_MDT.dtm")
		MDTtif = str(LAZ_MDTtif+"/"+laz[0:-4]+"_MDT.tif")

		if MDE == True:
			print ("Creando MDE")
			processing.runalg("lidartools:canopymodel",lazdir,Resolucion,0,0,"","","","",False,True,"",MDEdtm)
			time.sleep(1)
			# convertir asc en tif y extension del raster (servira para los procesos posteriores)
			rasterlayer = QgsRasterLayer(MDEasc,"rasterlayer")
			rasterext = rasterlayer.extent()
			xmin = rasterext.xMinimum()
			xmax = rasterext.xMaximum()
			ymin = rasterext.yMinimum()
			ymax = rasterext.yMaximum()
			extension = "%f,%f,%f,%f" %(xmin, xmax, ymin, ymax)
			processing.runalg("gdalogr:translate",MDEasc,100,True,"",0,"EPSG:25829",extension,False,5,4,75,6,1,False,0,False,"",MDEtif)
			
			# cambiar null por 0 y crear los tif
			processing.runalg("saga:reclassifygridvalues",MDEasc,0,0,1,0,0,1,2,0,"0,0,0,0,0,0,0,0,0",0,True,0,False,0,MDEmar)
			processing.runalg("gdalogr:translate",MDEmar,100,True,"",0,"EPSG:25829",extension,False,5,4,75,6,1,False,0,False,"",MDEmartif)

		# MDT -- usar FUSION crear superficie TIN seleccionando solo la clase 2 (ground)
		if MDT == True:
			print ("Creando MDT")
			processing.runalg("lidartools:tinsurfacecreate",lazdir,Resolucion,0,0,"2","",MDTdtm)
			processing.runalg("gdalogr:translate",MDTdtm,100,True,"",0,"EPSG:25829",extension,False,5,4,75,6,1,False,0,False,"",MDTtif)

			
#UNIR ARCHIVOS RASTER Y CREAR HS Y EL MDEnorm
	MDEtif2 = str(Output+'/'+'MDEtif.tif')
	MDEmartif2 = str(Output+'/'+'MDEmartif.tif')
	MDTtif2 = str(Output+'/'+'MDTtif.tif')
	MDEn = str(Output+"/"+"MDEnorm.tif")
	MDE_hs = str(Output+"/"+"MDE_hs.tif")

	#merge MDEtif2
	l=list()
	for f in os.listdir(LAZ_MDEtif):
		if f.endswith('.tif'):
			filedir = str(LAZ_MDEtif+'/'+f)
			l.append(filedir)
	l1 = str(';'.join(l))
	processing.runalg("gdalogr:merge",l1,False,False,-9999,5,MDEtif2)
	
	#merge MDEmartif2
	l=list()
	for f in os.listdir(LAZ_MDEmartif):
		if f.endswith(".tif"):
			filedir = str(LAZ_MDEmartif+'/'+f)
			l.append(filedir)
	l2 = str(';'.join(l))
	processing.runalg("gdalogr:merge",l2,False,False,-9999,5,MDEmartif2)

	#merge MDTtif2
	l=list()
	for f in os.listdir(LAZ_MDTtif):
		if f.endswith(".tif"):
			filedir = str(LAZ_MDTtif+'/'+f)
			l.append(filedir)
	l3 = str(';'.join(l))
	processing.runalg("gdalogr:merge",l3,False,False,-9999,5,MDTtif2)
	
	#MDEnorm MDE menos MDT con GDAL rastercalculator
	if MDEnorm == True:
		print ("Creando MDEnorm")
		processing.runalg("saga:rastercalculator",MDEmartif2,MDTtif2,"a-b",3,False,7,MDEn)

	#MDEhs para sombreado de alturas
	if MDEhs == True:
		print ("Creando MDE_hs")
		processing.runalg("gdalogr:hillshade",MDEtif2,1,False,False,1,1,315,45,MDE_hs)

