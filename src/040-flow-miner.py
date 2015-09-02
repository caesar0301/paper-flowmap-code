#!/usr/bin/env python
#
# @Xiaming Chen
import sys
import numpy as np
import time
import math
from datetime import datetime, date

class CellMap(object):
    def __init__(self, data):
        self._map = {}
        print("loading data ...")
        for line in open(data, 'rb'):
            parts = line.strip('\r\n ').split(',')
            id = int(parts[0])
            lon = float(parts[2])
            lat = float(parts[3])
            self._map[id] = (lon, lat)

    def id2coord(self, id):
        return self._map[id]

    def ids2coords(self, locs):
        return [ self._map[i] for i in locs ]

def drange(ts):
    dt = datetime.fromtimestamp(ts)
    if dt.hour < 3:
        sds = datetime(dt.year, dt.month, dt.day-1, 3)
    else:
        sds = datetime(dt.year, dt.month, dt.day, 3)
    eds = sds.replace(day=sds.day+1)
    return (sds, eds)

def in_area(p, lb, rt):
    if p[0] >= lb[0] and p[0] <= rt[0] and p[1] >= lb[1] and p[1] <= rt[1]:
        return True
    return False

def is_valid_location(locid):
    """ Check if given location point is valid
    """
    HZ_LB = [120.03013, 30.13614]
    HZ_RT = [120.28597, 30.35318]
    coord = cmap.id2coord(locid)
    lon = coord[0]
    lat = coord[1]
    return in_area([lon, lat], HZ_LB, HZ_RT)

def extract_metaflow(loc):
    """ Extract metaflows from a location sequence
    """
    n = len(loc)
    flows = []
    if n < 3:
        return flows
    i = 0
    while i < n:
        isdup = True
        found = False
        for j  in range(i+1, n):
            if loc[j] != loc[i]:
                isdup = False
                continue
            if not isdup and loc[j] == loc[i]:
                found = True
                flows.append((i, j))
                deeper = extract_metaflow(loc[i+1:j])
                deeper = [(t[0]+i+1, t[1]+i+1) for t in deeper]
                flows.extend(deeper)
                break
        i = (j + 1) if found else (i + 1)
    return flows

def calculate_gcd(latlon1, latlon2):
    """ Calculate great circle distance
    """
    lon1 = math.radians(latlon1[1])
    lat1 = math.radians(latlon1[0])
    lon2 = math.radians(latlon2[1])
    lat2 = math.radians(latlon2[0])
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = (math.sin(dlat / 2))**2 + math.cos(lat1) * math.cos(lat2) * (math.sin(dlon / 2))**2
    c = 2 * math.asin(min(1, math.sqrt(a)))
    dist = 6371 * c
    return dist

def calculate_mp(lats, lons, w=None):
    if w is None:
        w = [ 1 for i in lats ]
    # calculate weighted mid-point
    lon = np.array([ math.radians(i) for i in lons ])
    lat = np.array([ math.radians(i) for i in lats ])
    w = np.array(w)
    x = np.cos(lat) * np.cos(lon)
    y = np.cos(lat) * np.sin(lon)
    z = np.sin(lat)
    tw = np.sum(w)
    mx = 1.0 * np.sum(x * w) / tw
    my = 1.0 * np.sum(y * w) / tw
    mz = 1.0 * np.sum(z * w) / tw
    lon_r = math.atan2(my, mx)
    hyp_r = math.sqrt(mx**2 + my**2)
    lat_r = math.atan2(mz, hyp_r)
    lon_d = math.degrees(lon_r)
    lat_d = math.degrees(lat_r)
    return (lat_d, lon_d)

def calculate_rg(lats, lons):
    """ Calculate the radius of gyration
    """
    dist = []
    latlons = set(zip(lats, lons))
    lats = [ i[0] for i in latlons ]
    lons = [ i[1] for i in latlons ]
    lat_d, lon_d = calculate_mp(lats, lons)
    for i in range(0, len(lons)):
        gcd = calculate_gcd((lat_d, lon_d), (lats[i], lons[i]))
        dist.append(gcd)
    dist = np.array(dist)
    rg = np.sqrt(np.sum(dist**2) / len(dist))
    return rg

def calculate_comdist(lats, lons):
    """ Calculate the commulative distance
    """
    pass

def calculate_mindist(lats, lons):
    """ Calculate the minimum distance to visit all places
    """
    pass

def is_max_metaflow(flow, flows, n):
    is_max = True
    for f in flows:
        if f[0] == 0 and f[1] == n-1:
            continue
        if f[0] < flow[0] and f[1] > flow[1]:
            is_max = False
            break
    return is_max

def extract_metaflow_features(ts, locs, flows):
    """
    @ts: timestamp sequence
    @locs: location ID sequence
    @flows: a list of detected metaflows
    """
    features = []
    coords = cmap.ids2coords(locs)
    lons = [ i[0] for i in coords ]
    lats = [ i[1] for i in coords ]
    rg_day = calculate_rg(lats, lons)
    thisdate = date.fromtimestamp(ts[0])
    day_id = int("%4d%02d%02d" % (thisdate.year, thisdate.month, thisdate.day))
    ff_id = -1
    for flow in flows:
        ff_features = {}
        flow_locs = locs[ flow[0]:flow[1]+1 ]
        flow_ts = ts[ flow[0]:flow[1]+1 ]
        flow_lons = lons[ flow[0]:flow[1]+1 ]
        flow_lats = lats[ flow[0]:flow[1]+1 ]
        flow_dists = [ calculate_gcd((flow_lats[i], flow_lons[i]),
                                     (flow_lats[i+1], flow_lons[i+1]))
                       for i in range(0, len(flow_locs)-1) ]

        ff_id += 1
        ff_len = len(flow_locs)
        ff_ulen = len(set(flow_locs))
        ff_time = max(flow_ts) - min(flow_ts)
        ff_dist = sum(flow_dists)
        ff_ismax = is_max_metaflow(flow, flows, ff_len)
        ff_rg = calculate_rg(flow_lats, flow_lons)
        ff_rgprc = 1.0 * ff_rg / rg_day

        # delta flow
        delta_flow_lons = []
        delta_flow_lats = []
        if flow[0] > 0:
            delta_flow_lons.extend(lons[0:flow[0]])
            delta_flow_lats.extend(lats[0:flow[0]])
        if flow[1] < len(lons)-1:
            delta_flow_lons.extend(lons[ flow[1]+1:len(lons) ])
            delta_flow_lats.extend(lats[ flow[1]+1:len(lats) ])
        ff_rgdlt = calculate_rg(delta_flow_lats, delta_flow_lons)
        ff_rgdlt = 0 if np.isnan(ff_rgdlt) else ff_rgdlt

        ff_features['id'] = ff_id
        ff_features['len'] = ff_len
        ff_features['ulen'] = ff_ulen
        ff_features['time'] = ff_time
        ff_features['dist'] = ff_dist
        ff_features['ismax'] = ff_ismax
        ff_features['rg'] = ff_rg
        ff_features['rgprc'] = ff_rgprc
        ff_features['rgdlt'] = ff_rgdlt
        ff_features['date'] = day_id
        ff_features['idx1'] = flow[0]
        ff_features['idx2'] = flow[1]

        features.append(ff_features)

    return features

header=False
silent=True
def dump_features(uid, features, file='metaflows.txt'):
    global header, silent
    if not header:
        header=True
        ofile = open(file, 'wb')
        ofile.write("UID,DATE,FID,LEN,ULEN,TIME,DIST,ISMAX,RG,RGPRC,RGDLT,IDX1,IDX2\n")
    ofile = open(file, 'ab')
    for f in features:
        format_str = "%d,%d,%d,%d,%d,%d,%.3f,%d,%.3f,%.3f,%.3f,%d,%d" % \
            (uid, f['date'], f['id'], f['len'], f['ulen'], f['time'],
             f['dist'], f['ismax'], f['rg'], f['rgprc'], f['rgdlt'],
             f['idx1'], f['idx2'])
        if not silent: print format_str
        ofile.write(format_str + '\n')
    ofile.close()

if __name__ == '__main__':
    i = 0
    buf_ts = []
    buf_lc = []
    last_uid = None
    last_sds = None

    if len(sys.argv) < 3:
        print("Usage: %s <movement> <bsmap>" % sys.argv[0])
        sys.exit(-1)

    movement = open(sys.argv[1], 'rb')
    cmap = CellMap(sys.argv[2])

    for line in movement:
        uid, ts, loc = line.strip('\r\n').split(',')[0:3]
        uid = int(uid); ts = int(float(ts)); loc = int(loc)
        dt = datetime.fromtimestamp(ts)
        sds, eds = drange(ts)

        if not is_valid_location(loc):
            # omit points outside city range
            continue

        if last_uid is None or uid == last_uid and sds == last_sds:
            buf_ts.append(ts)
            buf_lc.append(loc)
        else: # manipulate the buffer
            if buf_ts[-1] != buf_ts[0] + 86400:
                buf_ts.append(buf_ts[0] + 86400)
                buf_lc.append(buf_lc[0])
            flows = extract_metaflow(buf_lc)
            if len(flows) > 0:
                print "[%s] %d: %s" % (time.ctime(buf_ts[0]), last_uid, flows)
                features = extract_metaflow_features(buf_ts, buf_lc, flows)
                dump_features(last_uid, features)
            buf_ts = [ts]
            buf_lc = [loc]
            if i > 2500000:
                break
            i += 1
        last_uid = uid
        last_sds = sds

    flows = extract_metaflow(buf_lc)
    print("Done!")

if __name__ == '__main__':
    print("-----------Module test------------")
    print calculate_gcd((47.64828, -122.52963), (47.61168,  -122.33326))
    lat = [30.23412, 30.266203, 30.266203, 30.265251, 30.267384,
           30.267384, 30.266203, 30.266203, 30.266203, 30.267384,
           30.266203, 30.265251, 30.267384, 30.267384, 30.264925,
           30.25779, 30.256128, 30.256592, 30.25665, 30.241655,
           30.242035, 30.24256, 30.24, 30.237858, 30.235168, 30.23412]
    lon = [120.195305, 120.16932, 120.16932, 120.17233, 120.17016,
           120.17016, 120.16932, 120.16932, 120.16932, 120.17016,
           120.16932, 120.17233, 120.17016, 120.17016, 120.1709,
           120.17321, 120.17334, 120.17848, 120.17696, 120.17795,
           120.18491, 120.18684, 120.18853, 120.19241, 120.196434,
           120.195305]
    print calculate_rg(lat, lon)
