#!/usr/bin/env python
# By Xiaming Chen
# Fri Jul 17 11:36:18 CST 2015

import csv
import shapefile

# write to shapefile
w = shapefile.Writer(shapefile.POINT)
w.autoBalance=1
w.field('BSID', 'N', 8, 0)
w.field('LAC', 'N', 8, 0)
w.field('CI', 'N', 8, 0)

#HZ_LB = [120.03013, 30.13614]
#HZ_RT = [120.28597, 30.35318]
#OUTFILE = "mobilenetwork"

HZ_LB = [120.15023, 30.25214]
HZ_RT = [120.18265, 30.27848]
OUTFILE = "mobilenetwork"

def in_area(p, lb, rt):
    if p[0] >= lb[0] and p[0] <= rt[0] and p[1] >= lb[1] and p[1] <= rt[1]:
        return True
    return False

for i in csv.reader(open('../data/hcl_bm.dat', 'rb'), delimiter=','):
    bsid = int(i[0])
    lac = int(i[1][:-6])
    ci = int(i[1][-6:])
    lon = float(i[2])
    lat = float(i[3])

    # adding shift between baidu and osm
    lon = lon - 0.011
    lat = lat - 0.004

    if not in_area([lon, lat], HZ_LB, HZ_RT):
        continue

    print bsid, lac, ci, lon, lat
    w.point(lon, lat)
    w.record(bsid, lac, ci)

w.save(OUTFILE)
