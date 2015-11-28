#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# Extract and analyze the mobility Mesos using Apache Spark.
import sys, os
from datetime import datetime
from ctypes import addressof

from pyspark import SparkContext, SparkConf

from xoxo.roadnet import RoadNetwork
from xoxo.bsmap import BaseStationMap
from xoxo.permov import movement_reader
from xoxo.settings import HZ_ROADNET
from xoxo.utils import zippylib, dumps_mobgraph, loads_mobgraph
from xoxo.mesos import Mesos

__author__ = 'Xiaming Chen'
__email__ = 'chen@xiaming.me'


def record_splitter(r):
    uid, ts, bid = r.strip('\r\n ').split(',')
    return (int(uid), float(ts), int(bid))


def mobility_graphs(logiter, bsmap, roadnet, cmax=20, dates=None):
    """ Extract mobility graphs from a list of movement observations
    """
    results = []
    for person in movement_reader(logiter, bsmap):
        if person.which_day() not in dates:
            continue

        if cmax and len(set(person.locations)) > cmax:
            continue

        graph = person.convert2graph(roadnet)
        nlen = len(graph.nodes())
        if nlen > 1:
            results.append((person.id, person.dtstart, nlen, graph))

    return results


def gen_mesos(lg1, lg2):
    uid1, ts1, grp, g1 = lg1
    uid2, ts2, grp, g2 = lg2
    mesos = Mesos(g1, g2, 'dwelling', 'distance')
    return (grp, mesos.struct_dist(), mesos.mesos, uid1, uid2, ts1, ts2)


def gen_mesos_group(lgiter):
    for lg1 in lgiter:
        for lg2 in lgiter:
            yield gen_mesos(lg1, lg2)


def format_time(ts):
    return ts.strftime("%m%d")


def dump_stat(x):
    res = [str(i) for i in [x[0], x[1], x[3], x[4], format_time(x[5]), format_time(x[6])]]
    return '|'.join(res)


def dumps_mesos(G):
    return dumps_mobgraph(G, 'dwelling', 'distance')


def loads_mesos(S):
    return loads_mobgraph(S, 'dwelling', 'distance')


def main(sc):
    if len(sys.argv) < 5:
        print >> sys.stderr, '''
Usage: mesos-spark <movdata> <bsmap> <output> <dates>
    Note: dates is a comma separeted string list, e.g., 0822,0823
'''
        exit(-1)

    # Read movement records
    movDataRDD = sc.textFile(sys.argv[1])
    bsmap = BaseStationMap(sys.argv[2])
    output = sys.argv[3]
    dates = sys.argv[4].split(',')

    roadnet = RoadNetwork(HZ_ROADNET)
    roadnet = None

    # Extract mobility graphs
    mobgraphRDD = movDataRDD.map(lambda x: record_splitter(x))\
        .groupBy(lambda x: x[0])\
        .flatMap(lambda x: mobility_graphs(x[1], bsmap, roadnet, dates=dates))\
        .cache()

    # Save temp mobility graphs
    # mobgraphRDD.map(lambda x: '|'.join([str(x[0]), format_time(x[1]), str(x[2]), dumps_mesos(x[3])])).saveAsTextFile(output + '.mg')

    # Extract Mesoses
    groups = mobgraphRDD.groupBy(lambda x: x[2]).collect()

    group_dict = {}
    for c, mgs in groups:
        group_dict[c] = mgs

    def self_join(x):
        res = []
        if x[2] in group_dict:
            res = [(x, i) for i in group_dict[x[2]]]
        return res

    # Assume 8 executors, 24 vcores per executor, we
    # get the partition number of multiple of 8 x 24 = 192.
    pairsRDD = mobgraphRDD.keyBy(lambda x: (x))\
        .partitionBy(384)\
        .flatMap(lambda x: self_join(x[1]))\
        .keyBy(lambda x: (x[0], x[1]))\
        .partitionBy(1920)\
        .map(lambda x: dump_stat(gen_mesos(x[1][0], x[1][1])))

    pairsRDD.saveAsTextFile(output)


if __name__ == '__main__':
    APP_NAME = "MesosSparkJob"
    conf = SparkConf().setAppName(APP_NAME)
    sc = SparkContext(conf=conf)
    thisdir = os.path.dirname(__file__)

    # add external python libraries
    xoxoZip = zippylib(os.path.join(thisdir, 'xoxo'))
    sc.addPyFile(xoxoZip)

    # Distribute map files onto cluster before running
    main(sc)
