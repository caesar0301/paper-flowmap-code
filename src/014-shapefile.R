# create and resave the shapefiles
# see:
# http://xiaming.me/posts/2015/08/30/a-tutorial-on-topology-correction-of-shapefiles-using-grass/
library(shp2graph)

road_net <- readShapeLines("map/hz2/roads_snapped.shp", proj4string=CRS(as.character(NA)))
rn <- nt.connect(road_net) # main conponent
writeSpatialShape(rn, 'map/hz2/roads_clean.shp')

road_net <- readShapeLines("map/hz/roads_snapped.shp", proj4string=CRS(as.character(NA)))
rn <- nt.connect(road_net) # main conponent
writeSpatialShape(rn, 'map/hz/roads_clean.shp')