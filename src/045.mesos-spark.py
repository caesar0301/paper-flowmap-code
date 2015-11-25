#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# Extract and analyze the mobility Mesos using Apache Spark.
import sys, os
from datetime import datetime

from pyspark import SparkContext, SparkConf

from xoxo.roadnet import RoadNetwork
from xoxo.bsmap import BaseStationMap
from xoxo.permov import movement_extractor
from xoxo.settings import BSMAP, HZ_ROADNET
from xoxo.utils import zippylib, dumps_mobgraph, loads_mobgraph
from xoxo.mesos import Mesos

__author__ = 'Xiaming Chen'
__email__ = 'chen@xiaming.me'


def record_splitter(r):
    uid, ts, bid = r.strip('\r\n ').split(',')
    return (int(uid), float(ts), int(bid))


def mobility_graphs(logiter, bsmap, roadnet):
    results = []
    for person in movement_extractor(logiter, bsmap):
        graph = person.convert2graph(roadnet, True)
        nlen = len(graph.nodes())
        if nlen > 1:
            results.append((person.id, person.dtstart, nlen, graph))
    return results


def gen_mesos(lg1, lg2):
    uid1, ts1, grp, g1 = lg1
    uid2, ts2, grp, g2 = lg2
    mesos = Mesos(g1, g2, 'dwelling', 'distance')
    return (grp, mesos.struct_dist(), mesos.mesos, uid1, uid2, ts1, ts2)


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
    if len(sys.argv) < 3:
        print >> sys.stderr, "Usage: mesos-spark <movdata> <output>"
        exit(-1)

    GROUP_FOLD = 10

    # Read movement records
    movDataRDD = sc.textFile(sys.argv[1], 1)
    output = sys.argv[2]

    bsmap = BaseStationMap(BSMAP)
    roadnet = RoadNetwork(HZ_ROADNET)

    # Extract mobility graphs
    mobgraphRDD = movDataRDD.map(lambda x: record_splitter(x))\
        .groupBy(lambda x: x[0])\
        .flatMap(lambda x: mobility_graphs(x[1], bsmap, roadnet))\
        .cache()

    # Save temp mobility graphs
    mobgraphRDD.map(lambda x: '|'.join([str(x[0]), format_time(x[1]), str(x[2]), dumps_mesos(x[3])]))\
        .saveAsTextFile(output + '.mg')

    # Extract Mesoses
    mobgraphRDD = mobgraphRDD.keyBy(lambda x: x[2]) # (keyed by graph caidinality)
    groups = mobgraphRDD.join(mobgraphRDD)
    mesosRDD = groups.map(lambda x: gen_mesos(x[1][0], x[1][1]))

    # Dump to disk
    mesosRDD.map(lambda x: dump_stat(x)).saveAsTextFile(output)


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
