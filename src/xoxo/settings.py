DEBUGGING = True

# Movement history
MOVEMENT_HIST = 'data/hcl.dat'

# Base station map
BSMAP = 'data/hcl_bm.dat'

# Max user number
if DEBUGGING:
    MAX_USER_NUM = 1
else:
    MAX_USER_NUM = 1000000000

# Road shapefile of HZ
HZ_SHAPEFILE = 'map/hz/roads_clean.shp'
HZ_MOBILE_SHAPEFILE = 'map/hz/mobilenetwork.shp'