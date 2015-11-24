import os

DEBUGGING = False

thisdir = os.path.dirname(__file__)

MOVEMENT_DAT = os.path.join(thisdir, '../../data/hcl.dat')
BSMAP = os.path.join(thisdir, '../../data/hcl_bm.dat')
HZ_ROADNET = os.path.join(thisdir, '../../map/hz/roads_clean.shp')
HZ_MOBNET = os.path.join(thisdir, '../../map/hz/mobilenetwork.shp')

# For spark
# BSMAP = '/tmp/hcl_bm.dat'
# HZ_ROADNET = '/tmp/map/hz/roads_clean.shp'

HZ_LB = [120.03013, 30.13614]
HZ_RT = [120.28597, 30.35318]

if DEBUGGING:
    MAX_USER_NUM = 1
else:
    MAX_USER_NUM = 1000000000