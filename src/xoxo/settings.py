DEBUGGING = True

# Movement history
MOVEMENT_HIST = 'data/hcl.dat'

# Base station map
BSMAP = 'data/hcl_bm.dat'

# Max user number
if DEBUGGING:
    MAX_USER_NUM = 10
else:
    MAX_USER_NUM = 1000000000

# Road shapefile of HZ
HZ_SHAPEFILE = 'map/hz/roads_clean.shp'
HZ_MOBILE_SHAPEFILE = 'map/hz/mobilenetwork.shp'

HZ_LB = [120.03013, 30.13614]
HZ_RT = [120.28597, 30.35318]