#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# Extract and analyze the mobility Mesos using Apache Spark.
import sys, os

import numpy as np

from xoxo.bsmap import BaseStationMap
from xoxo.permov import movement_reader
from xoxo.utils import radius_of_gyration

__author__ = 'Xiaming Chen'
__email__ = 'chen@xiaming.me'


def format_time(ts):
    return ts.strftime("%m%d")


def daily_rg(movdata, bsmap, output):
    """ R_g for one day
    """
    bsmap = BaseStationMap(bsmap)

    res = {}
    for person in movement_reader(open(movdata, 'rb'), bsmap):
        uid = person.id
        tdate = person.dtstart.strftime("%m%d")
        rg = person.radius_of_gyration()
        if tdate not in res:
            res[tdate] = []
        res[tdate].append((uid, rg))

    for tdate in res:
        try:
            os.mkdir(output)
        except:
            pass
        ofile = open(os.path.join(output, tdate), 'wb')
        [ofile.write('%d,%.4f\n' % (i[0],i[1])) for i in sorted(res[tdate], key=lambda x: x[0])]
        ofile.close()


def accu_rg(movdata, bsmap, output):
    """ Accumulative R_g over multiple days
    """
    bsmap = BaseStationMap(bsmap)

    dates = {'0820': 0, '0821': 1, '0822': 2, '0823': 3, '0824': 4, '0825': 5, '0826': 6}

    res = {}
    coords = {}
    for person in movement_reader(open(movdata, 'rb'), bsmap):
        uid = person.id
        tdate = person.which_day()
        if tdate not in dates:
            continue

        if uid not in coords:
            coords[uid] = person.coordinates
        else:
            coords[uid].extend(person.coordinates)

        if uid not in res:
            res[uid] = np.empty(7)
            res[uid].fill(-1)

        res[uid][dates[tdate]] = radius_of_gyration(coords[uid])

    res2 = []
    for uid in res:
        v = res[uid]
        v2 = []
        for n in v:
            if n == -1:
                try:
                    v2.append(v2[-1])
                except:
                    v2.append(0)
            else:
                v2.append(n)
        res2.append((uid, v2))
    res2 = sorted(res2, key=lambda x: x[0])

    ofile = open(output, 'wb')
    [ofile.write('%d,%s\n' % (i[0], ','.join(['%.4f' % j for j in i[1]]))) for i in res2]
    ofile.close()


def accu_dt(movdata, bsmap, output, log=True):
    """ Distribution of dwelling time for each person
    """
    bsmap = BaseStationMap(bsmap)

    res = {}
    for person in movement_reader(open(movdata, 'rb'), bsmap):
        uid = person.id
        dt = person.accdwelling.values()
        if uid not in res:
            res[uid] = dt
        else:
            res[uid].extend(dt)

    ofile = open(output, 'wb')
    if log is True:
        bins = np.logspace(-2,2,50)
    else:
        bins = np.arange(0,24.5,0.5)

    if log is True:
        ofile.write('#bins np.logspace(-2,2,50)\n')
    else:
        ofile.write('#bins np.arange(0,24.5,0.5)\n')

    for uid in res:
        hist = np.histogram(np.array(res[uid])/3600, bins=bins)[0]
        ofile.write('%d,%s\n' % (uid, ','.join([str(h) for h in hist])))
    ofile.close()


def loc_dt(movdata, bsmap, output, log=True):
    """ Distribution of dwelling time for each person, each location
    """
    bsmap = BaseStationMap(bsmap)

    res = {}
    for person in movement_reader(open(movdata, 'rb'), bsmap):
        uid = person.id
        dt = person.accdwelling
        if uid not in res:
            res[uid] = {}
        for k, v in dt.items():
            if k not in res[uid]:
                res[uid][k] = []
            res[uid][k].append(v)

    ofile = open(output, 'wb')
    if log is True:
        bins = np.logspace(-2,2,50)
    else:
        bins = np.arange(0,24.5,0.5)

    if log is True:
        ofile.write('#bins np.logspace(-2,2,50)\n')
    else:
        ofile.write('#bins np.arange(0,24.5,0.5)\n')

    for uid in res:
        vs = [np.average(v) for k, v in res[uid].items()]
        hist = np.histogram(np.array(vs)/3600, bins=bins)[0]
        ofile.write('%d,%s\n' % (uid, ','.join([str(h) for h in hist])))
    ofile.close()


def loc_dt_all(movdata, bsmap, output):
    """ All raw dwelling times for each person, each location
    """
    bsmap = BaseStationMap(bsmap)

    res = {}
    for person in movement_reader(open(movdata, 'rb'), bsmap):
        uid = person.id
        dt = person.accdwelling
        if uid not in res:
            res[uid] = {}
        for k, v in dt.items():
            if k not in res[uid]:
                res[uid][k] = []
            res[uid][k].append(v)

    ofile = open(output, 'wb')
    for uid in res:
        vs = sorted([np.average(v)/3600 for k, v in res[uid].items()], reverse=True)
        ofile.write('%d,%s\n' % (uid, ','.join(['%.3f' % v for v in vs])))
    ofile.close()


def mobgraph_degree(movdata, bsmap, output):
    """ Node degree of mobility graphs
    """
    nloc = []
    ndgr = []
    bsmap = BaseStationMap(bsmap)

    for person in movement_reader(open(movdata, 'rb'), bsmap):
        if person.distinct_loc_num() < 2:
            continue

        graph = person.convert2graph()
        ndgr.append(np.mean(graph.degree().values()))
        nloc.append(person.distinct_loc_num())

    ofile = open(output, 'wb')
    ofile.write('nloc,ndgr\n')
    ofile.write('\n'.join( ['%d,%.3f' % (x,y) for x, y in zip(nloc, ndgr)]))


def main():
    if len(sys.argv) < 4:
        print >> sys.stderr, "Usage: mesos <movdata> <bsmap> <output>"
        exit(-1)

    movdata = sys.argv[1]
    bsmap = sys.argv[2]
    output = sys.argv[3]

    # daily_rg(movdata, bsmap, output)
    # accu_rg(movdata, bsmap, output)
    # accu_dt(movdata, bsmap, output)
    # loc_dt(movdata, bsmap, output)
    # loc_dw_all(movdata, bsmap, output)
    mobgraph_degree(movdata, bsmap, output)


if __name__ == '__main__':
    main()
