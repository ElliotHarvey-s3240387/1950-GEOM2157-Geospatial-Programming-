#finalProject

#filepath
filepath = "C:/Users/Harvey/Documents/GIS Programming/Final Report/Data Files/"

#filenames
waterFileName = "HY_WATERCOURSE.shp"
treeFileName = "TREE_DENSITY.shp"
ptvFileName = "PTV_METRO_BUS_ROUTE.shp"
contourFileName = "EL_CONTOUR.shp"
yvFileName = "EXTRACT_POLYGON_YV.shp"
csFileName = "EXTRACT_POLYGON_CS.shp"
pointFileName = "PointGrid.shp"


#Merge Region
yvLayer = iface.addVectorLayer(filepath + yvFileName, yvFileName[:-4], "ogr")
csLayer = iface.addVectorLayer(filepath + csFileName, csFileName[:-4], "ogr")

mergeDict = {"LAYERS":[yvLayer, csLayer], "CRS": '', "OUTPUT": filepath + "merge.shp"}
processing.run('native:mergevectorlayers', mergeDict)
mergeLayer = iface.addVectorLayer(filepath + "merge.shp", '', "ogr")


#Select Tree_Den other than Scattered
treeLayer = iface.addVectorLayer(filepath + treeFileName, treeFileName[:-4], "ogr")
selectDict = {"INPUT":treeLayer, "FIELD":"TREE_DEN", "OPERATOR": 10, "VALUE": "SCATTERED", "METHOD": 0} 
processing.run('qgis:selectbyattribute', selectDict)

#Extract Select
extractDict = {"INPUT":treeLayer, "OUTPUT": filepath + "TREE_DENSE_MED_HEAVY.shp"}
processing.run('native:saveselectedfeatures', extractDict)
tree2Layer = iface.addVectorLayer(filepath + "TREE_DENSE_MED_HEAVY.shp", '', "ogr")

#fix geometry
fixDict = {"INPUT":tree2Layer, "OUTPUT": filepath + "TREE_FIXED.shp"}
processing.run('native:fixgeometries', fixDict)
fixedLayer = iface.addVectorLayer(filepath + "TREE_FIXED.shp", '', "ogr")


#Difference tree layer from region merge
differenceDict = {"INPUT":mergeLayer, "OVERLAY":fixedLayer, "OUTPUT": filepath + "REGION_MINUS_TREE.shp"}
processing.run('native:difference', differenceDict)
notreeLayer = iface.addVectorLayer(filepath + "REGION_MINUS_TREE.shp", '', "ogr")



#buffer stream/creeks
waterLayer = iface.addVectorLayer(filepath + waterFileName, waterFileName[:-4], "ogr")
buffDict = {"INPUT":waterLayer, "DISTANCE": 20, "SEGMENTS": 1, "END_CAP_STYLE": 0, "JOIN_STYLE": 0, "MITER_LIMIT": 2, "DISSOLVE": True, "OUTPUT": filepath + "buff.shp"}
processing.run('native:buffer', buffDict)
buffLayer = iface.addVectorLayer(filepath + "buff.shp", '', "ogr")

#Difference water layer from region without trees
difference2Dict = {"INPUT":notreeLayer, "OVERLAY":buffLayer, "OUTPUT": filepath + "REGION_MINUS_TREE_WATER.shp"}
processing.run('native:difference', difference2Dict)
notreewaterLayer = iface.addVectorLayer(filepath + "REGION_MINUS_TREE_WATER.shp", '', "ogr")

#trim route layer
routeLayer = iface.addVectorLayer(filepath + ptvFileName, ptvFileName[:-4], "ogr")
routeclipDict = {"INPUT":routeLayer, "OVERLAY":mergeLayer, "OUTPUT": filepath + "ROUTE_CLIP.shp"}
processing.run('native:clip', routeclipDict)
routeclipLayer = iface.addVectorLayer(filepath + "ROUTE_CLIP.shp", '', "ogr")

#dissolve route layer
dissolveDict = {"INPUT":routeclipLayer, "OUTPUT": filepath + "DISSOLVE.shp"}
processing.run('native:dissolve', dissolveDict)
dissolveLayer = iface.addVectorLayer(filepath + "DISSOLVE.shp", '', "ogr")

#multi-ring buff the dissolved route layer
multibuffDict = {"INPUT":dissolveLayer, "RINGS":10, "DISTANCE":250, "OUTPUT": filepath + "MULTI_BUFF.shp"}
processing.run('native:multiringconstantbuffer', multibuffDict)
multibuffLayer = iface.addVectorLayer(filepath + "MULTI_BUFF.shp", '', "ogr")

#clip multi-buffer with region file that has tree/water removed
clipbuffDict = {"INPUT":multibuffLayer, "OVERLAY":notreewaterLayer, "OUTPUT": filepath + "CLIPPED_BUFF.shp"}
processing.run('native:clip', clipbuffDict)
clipbuffLayer = iface.addVectorLayer(filepath + "CLIPPED_BUFF.shp", '', "ogr")


#Intersect custom created point grid with clipped multi-buffer so that only points that fall within clipped area remainingTime
#Remaining points also inherent distance based on buff ring they fall into
pointLayer = iface.addVectorLayer(filepath + pointFileName, pointFileName[:-4], "ogr")
intersectDict = {"INPUT":pointLayer, "OVERLAY":clipbuffLayer, "INPUT_FIELDS":'id', "OVERLAY_FIELDS":'distance', "OVERLAY_FIELDS_PREFIX":'', "OUTPUT": filepath + "POINT_INTERSECT.shp"}
processing.run('native:intersection', intersectDict)
pointintLayer = iface.addVectorLayer(filepath + "POINT_INTERSECT.shp", '', "ogr")



#fix geometry of original tree layer
fix2Dict = {"INPUT":treeLayer, "OUTPUT": filepath + "TREE_FIXED_TWO.shp"}
processing.run('native:fixgeometries', fix2Dict)
fixed2Layer = iface.addVectorLayer(filepath + "TREE_FIXED_TWO.shp", '', "ogr")


#intersect the second fixed tree layer with new point files.
#new points can't fall anywhere but on "scattered" clusters due to previouse steps
intersecttreeDict = {"INPUT":pointintLayer, "OVERLAY":fixed2Layer, "OVERLAY_FIELDS":'TREE_DEN', "OVERLAY_FIELDS_PREFIX":'', "OUTPUT": filepath + "POINT_TREE_INTERSECT.shp"}
processing.run('native:intersection', intersecttreeDict)
pointtreeintLayer = iface.addVectorLayer(filepath + "POINT_TREE_INTERSECT.shp", '', "ogr")

#merge the two point layers. Unfortunatly, could not figure out way to prevent duplicate points
merge2Dict = {"LAYERS":[pointintLayer, pointtreeintLayer], "CRS": '', "OUTPUT": filepath + "MERGED_POINTS.shp"}
processing.run('native:mergevectorlayers', merge2Dict)
mergedpointsLayer = iface.addVectorLayer(filepath + "MERGED_POINTS.shp", '', "ogr")

#add attribute field to Merged Points "viability"
addfieldDict = {"INPUT":mergedpointsLayer, "FIELD_NAME":'Viability', "FIELD_TYPE": 2, "FIELD_LENGTH": 10, "FIELD_PRECISION": 0, "OUTPUT": filepath + "FINAL.shp"}
processing.run('qgis:addfieldtoattributestable', addfieldDict)
FinalLayer = iface.addVectorLayer(filepath + "FINAL.shp", '', "ogr")

count = 0
via = ''
distance = ''
tree = ''

#loop to fill out viability table 
zones = FinalLayer.getFeatures()

for zone in zones:
    tree = zone["TREE_DEN"]
    distance = zone["distance"]
    

#Set count for how far away point is from route        
    if (distance == 2500):
        count = 5
    elif (distance > 2000):
        count = 4
    elif (distance > 1500):
        count = 3
    elif (distance > 1000):
        count = 2
    elif (distance > 500):
        count = 1
    else:
        count = 0
        
#Add +2 to count if points fall apon an area of scattered trees.
    if (tree == 'SCATTERED'):
        count = count + 2
    else:
        pass
        
    if (count == 0):
        via = "Most Viable" 
    elif (count == 1):
        via = "Very Viable"
    elif (count == 2):
        via = "Viable"
    elif (count == 3):
        via = "Potentially Viable"
    elif (count == 4):
        via = "Not Recomended"
    elif (count == 5):
        via = "Not Viable" 
    elif (count == 6):
        via = "Very not Viable"
    elif (count == 7):
        via = "Oof" 
    else:
        pass
        
    FinalLayer.startEditing()
    zone["Viability"] = via
    FinalLayer.updateFeature(zone)
count = 0

FinalLayer.commitChanges()














