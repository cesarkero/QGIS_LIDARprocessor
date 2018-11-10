##LIDAR=group
##LIDARprocessorV2=name
##Buffer=vector
##Catalog=vector
##Output=folder
##MDEnorm=boolean TRUE
##Hillshades=boolean TRUE
##Resolucion=number 1
##EliminarLAZfilesCopiados=boolean FALSE

from PyQt4.QtCore import QFileInfo, QSettings, QVariant
from qgis.core import *
import qgis.utils
import os, glob, processing, string, time, shutil, os.path

Buffer = "Z:/Proxectos/589_astillero_4_0/5_gis/shp/Buffers/Buffer_5000.shp"
Catalog= "Z:/Proxectos/589_astillero_4_0/5_gis/shp/LIDAR_catalog.shp"
Output = "Z:/Proxectos/589_astillero_4_0/5_gis/paisaje/LIDAR_5km_20183004"
Resolucion = 1
MDEnorm = bool(1)
Hillshades = bool(1)
EliminarLAZfilesCopiados = bool (0)

settings = QSettings()
# Take the "CRS for new layers" config, overwrite it while loading layers and...
oldProjValue = settings.value( "/Projections/defaultBehaviour", "prompt", type=str )
settings.setValue( "/Projections/defaultBehaviour", "useProject" )

# Crear estructuras de carpetas, comprobando si ya estaban hechas para no rehacerlas
LAZ_files = str(Output+'/'+'_00_LAZ_files/')
LAZ_tiles = Output+'/'+'_01_LAZ_tiles/'
LAZ_MDE = str(Output+'/'+'_02_LAZ_MDE')
LAZ_MDEtif = str(Output+'/'+'_03_LAZ_MDEtif')
LAZ_MDT = str(Output+'/'+'_04_LAZ_MDT')
LAZ_MDTtif = str(Output+'/'+'_05_LAZ_MDTtif')
carpetas=[LAZ_files,LAZ_tiles,LAZ_MDE,LAZ_MDEtif,LAZ_MDT,LAZ_MDTtif]

for c in carpetas:
	if os.path.isdir(c) is not True:
		os.mkdir(c)
	else:
		print("El directorio "+c+" ya existe")

#seleccionar entidades del shp LIDAR_catalogo (debe estar cargado en canvas y con el mismo nombre LIDAR_catalog)
print ("Recorte de catalogo con buffer")
recorte= str(LAZ_files+"/"+"LAZ_files.shp")
if os.path.isfile(recorte) is not True:
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
Filelist = list()
Pathlist = list()
count=0

#crear lista de valores unicos y append path (Pathlist sera la lista de archivos laz a procesar)
for f in files:
	if f not in Filecheck:
		Filecheck.append(f)
		Pathlist.append(paths[count])
		Filelist.append(files[count])
	count+=1
Pathlist2 = ';'.join(Pathlist)

count=0		
for f in Filelist:
	filecopy = str(LAZ_files+'/'+f)
	if os.path.isfile(filecopy) is not True:
		print ("Copiando "+f)
		shutil.copy2(Pathlist[count],LAZ_files)
	count+=1

#ejecutar lastiles
#crear listas de procesado para raster virtual
MDElist = list()
MDTlist = list()
print ("Ejecutando lastile")	
if os.listdir(LAZ_tiles) == []: 
    processing.runalg("lidartools:lastilepro",LAZ_files,"*.laz",False,False,5000,75,True,False,LAZ_tiles,"LAZ.laz",0,"",False,False) 

for laz in os.listdir(LAZ_tiles):
	lazdir = str(LAZ_tiles+'/'+laz)
	# MDE usar FUSION canopy model a 1 m y crear asc y dtm
	MDEdtm = str(LAZ_MDE+"/"+laz[0:-4]+"_MDE.dtm")
	MDEasc = str(LAZ_MDE+"/"+laz[0:-4]+"_MDE.asc")
	MDEtif = str(LAZ_MDEtif+"/"+laz[0:-4]+"_MDE.tif")
	MDTground = str(LAZ_MDT+"/"+laz[0:-4]+"_ground.laz")
	MDTgrounddtm = str(LAZ_MDT+"/"+laz[0:-4]+"_ground_ground_surface.dtm")
	MDTgrounddtmasc = str(LAZ_MDT+"/"+laz[0:-4]+"_ground_ground_surface.asc")
	MDTgroundtin = str(LAZ_MDT+"/"+laz[0:-4]+"_groundtin.dtm")
	MDTtif = str(LAZ_MDTtif+"/"+laz[0:-4]+"_MDT.tif")
	#Crear canopy model con FUSION
	if os.path.isfile(MDEdtm) is not True:
		print ("Creando MDE")
		processing.runalg("lidartools:canopymodel",lazdir,Resolucion,0,0,"","","","",False,True,"",MDEdtm)
		
	#convertir MDEdtm en MDEtif y listar archivos tif
	#ACTUALIZACION: se recorta el raster 40m a cada lado para eliminar los bordes problematicos
	if os.path.isfile(MDEtif) is not True:
		print ("Recordanto MDEtif")
		rasterlayer = QgsRasterLayer(MDEasc,"rasterlayer")
		rasterext = rasterlayer.extent()
		xmin = rasterext.xMinimum()+50
		xmax = rasterext.xMaximum()-50
		ymin = rasterext.yMinimum()+50
		ymax = rasterext.yMaximum()-50
		extension = "%f,%f,%f,%f" %(xmin, xmax, ymin, ymax)
		processing.runalg("gdalogr:translate",MDEasc,100,True,"",0,"EPSG:25829",extension,False,5,4,75,6,1,False,0,False,"",MDEtif)
		MDElist.append(MDEtif)
	#MDT
	if os.path.isfile(MDTground) is not True:
		print ("groundfilter")
		processing.runalg("lidartools:groundfilter",lazdir,5,True,"",MDTground)
	if os.path.isfile(MDTgrounddtmasc) is not True:
		print ("Crando grounddtmasc")
		processing.runalg("lidartools:dtmtoascii",MDTgrounddtm,0)
	if os.path.isfile(MDTgroundtin) is not True: 
		print ("Creando groundtin")
		processing.runalg("lidartools:tinsurfacecreate",MDTground,5,0,0,"2","",MDTgroundtin)
	#debido a que a veces tinsurface falla, se se incorpora un else para usar el asc salido de grounddtmasc
	if os.path.isfile(MDTtif) is not True:
		if os.path.isfile(MDTgroundtin) is True:
			print ("Recortando MDTtif")
			rasterlayer = QgsRasterLayer(MDTgroundtin,"rasterlayer")
			rasterext = rasterlayer.extent()
			xmin = rasterext.xMinimum()+50
			xmax = rasterext.xMaximum()-50
			ymin = rasterext.yMinimum()+50
			ymax = rasterext.yMaximum()-50
			extension = "%f,%f,%f,%f" %(xmin, xmax, ymin, ymax)
			processing.runalg("gdalogr:translate",MDTgroundtin,100,True,"",0,"EPSG:25829",extension,False,5,4,75,6,1,False,0,False,"",MDTtif)
			MDTlist.append(MDTtif)
		else:
			print ("Recortando MDTtif")
			rasterlayer = QgsRasterLayer(MDTgrounddtmasc,"rasterlayer")
			rasterext = rasterlayer.extent()
			xmin = rasterext.xMinimum()+50
			xmax = rasterext.xMaximum()-50
			ymin = rasterext.yMinimum()+50
			ymax = rasterext.yMaximum()-50
			extension = "%f,%f,%f,%f" %(xmin, xmax, ymin, ymax)
			processing.runalg("gdalogr:translate",MDTgrounddtmasc,100,True,"",0,"EPSG:25829",extension,False,5,4,75,6,1,False,0,False,"",MDTtif)
			MDTlist.append(MDTtif)

		
if MDEnorm == True:
	#Crear raster virtual y MDEnorm
	MDElist2 = ';'.join(MDElist)
	MDTlist2 = ';'.join(MDTlist)

	#MDE virtual
	print ("Creando MDE virtual")
	MDEvirtual = str(Output+'/'+'MDE.vrt')
	if os.path.isfile(MDEvirtual) is not True:
		#Proceso con llamada a la interfaz de GIS (distinto a los runalg)
		MDEtifdir = str(LAZ_MDEtif+'/'+ "*.tif")
		os.system("gdalbuildvrt -a_srs EPSG:25829 "+ MDEvirtual+' '+ MDEtifdir)
		
	#MDT virtual
	print ("Creando MDT virtual")
	MDTvirtual = str(Output+'/'+'MDT.vrt')
	if os.path.isfile(MDTvirtual) is not True:
		MDTtifdir = str(LAZ_MDTtif+'/'+ "*.tif")
		os.system("gdalbuildvrt -a_srs EPSG:25829 "+ MDTvirtual+' '+ MDTtifdir)
	
	#MDEnorm
	print ("Creando MDEnorm")
	MDEnormtif = str(Output+'/'+'MDEnorm.tif')
	if os.path.isfile(MDEnormtif) is not True:
		processing.runalg("saga:rastercalculator",MDEvirtual,MDTvirtual,"a-b",0,False,7,MDEnormtif)

if MDEnorm == True: 
	if Hillshades == True:
		# MDEhs para sombreado de alturas
		print ("Creando MDE hillshade")
		MDE_hs = str(Output+'/'+'MDE_hs.tif')
		if os.path.isfile(MDE_hs) is not True:
			print ("Creando MDE_hs")
			processing.runalg("gdalogr:hillshade",MDEvirtual,1,False,False,1,1,315,45,MDE_hs)
		
		print ("Creando MDT hillshade")
		MDT_hs = str(Output+'/'+'MDT_hs.tif')
		if os.path.isfile(MDT_hs) is not True:
			print ("Creando MDEnorm_hs")
			processing.runalg("gdalogr:hillshade",MDTvirtual,1,False,False,1,1,315,45,MDT_hs)

#eliminar carpeta con archivos laz copiados
if EliminarLAZfilesCopiados == True:
	print ("Borrando ./_00_LAZ_files/")
	shutil.rmtree(LAZ_files,ignore_errors=True)
	
settings.setValue( "/Projections/defaultBehaviour", oldProjValue )
