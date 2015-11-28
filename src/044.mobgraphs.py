#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# Extract and analyze the mobility Mesos using Apache Spark.
import sys, os
from datetime import datetime

from pyspark import SparkContext, SparkConf

from xoxo.roadnet import RoadNetwork
from xoxo.bsmap import BaseStationMap
from xoxo.permov import movement_reader
from xoxo.settings import BSMAP, HZ_ROADNET
from xoxo.utils import zippylib, dumps_mobgraph, loads_mobgraph

__author__ = 'Xiaming Chen'
__email__ = 'chen@xiaming.me'


def record_splitter(r):
    uid, ts, bid = r.strip('\r\n ').split(',')
    return (int(uid), float(ts), int(bid))


def mobility_graphs(logiter, bsmap, roadnet):
    results = []
    for person in movement_reader(logiter, bsmap):
        graph = person.convert2graph(roadnet, True)
        nlen = len(graph.nodes())
        if nlen > 1:
            results.append((person.id, person.dtstart, nlen, graph))
    return results


def format_time(ts):
    return ts.strftime("%m%d")


def dumps_mesos(G):
    return dumps_mobgraph(G, 'dwelling', 'distance')


def loads_mesos(S):
    return loads_mobgraph(S, 'dwelling', 'distance')


def main(sc):
    if len(sys.argv) < 3:
        print >> sys.stderr, "Usage: mg-spark <movdata> <output>"
        exit(-1)

    # Read movement records
    movDataRDD = sc.textFile(sys.argv[1], 1)
    output = sys.argv[2]

    bsmap = BaseStationMap(BSMAP)
    roadnet = RoadNetwork(HZ_ROADNET)

    # Extract mobility graphs
    movDataRDD.map(lambda x: record_splitter(x))\
        .groupBy(lambda x: x[0])\
        .flatMap(lambda x: mobility_graphs(x[1], bsmap, roadnet))\
        .map(lambda x: '|'.join([str(x[0]), format_time(x[1]), str(x[2]), dumps_mesos(x[3])]))\
        .saveAsTextFile(output + '.mg')


if __name__ == '__main__':
    APP_NAME = "ExtractMobilityGraphs"
    conf = SparkConf().setAppName(APP_NAME)
    sc = SparkContext(conf=conf)
    thisdir = os.path.dirname(__file__)

    # add external python libraries
    xoxoZip = zippylib(os.path.join(thisdir, 'xoxo'))
    sc.addPyFile(xoxoZip)

    main(sc)
