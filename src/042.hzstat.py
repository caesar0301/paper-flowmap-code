#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# Extract and analyze the mobility Mesos using Apache Spark.
import sys
import os

from pyspark import SparkContext, SparkConf

from xoxo.bsmap import BaseStationMap
from xoxo.permov import movement_reader
from xoxo.settings import BSMAP
from xoxo.utils import zippylib

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

def main(sc):
    if len(sys.argv) < 3:
        print >> sys.stderr, "Usage: hzstat <movdata> <output>"
        exit(-1)

    # Read movement records
    movDataRDD = sc.textFile(sys.argv[1])
    output = sys.argv[2]

    bsmap = BaseStationMap(BSMAP)

    movDataRDD = movDataRDD.map(lambda x: record_splitter(x))

    sc.parallelize([movDataRDD.count()], 1).saveAsTextFile(os.path.join(output, 'totalrecords'))

    sc.parallelize([movDataRDD.map(lambda x: x[2]).distinct().count()], 1).saveAsTextFile(os.path.join(output, 'totalbs'))

    # Extract mobility graphs
    mobgraphRDD = movDataRDD.groupBy(lambda x: x[0]).flatMap(lambda x: mobility_graphs(x[1], bsmap, None))

    sc.parallelize([mobgraphRDD.count()], 1).saveAsTextFile(os.path.join(output, 'totalmgs'))

    sc.parallelize([mobgraphRDD.map(lambda x: x[0]).distinct().count()], 1).saveAsTextFile(os.path.join(output, 'totalusers'))

    def group_stat(mgiter):
        totalusers = len(set([i[0] for i in mgiter]))
        totalgraphs = len([i[3] for i in mgiter])
        return (totalusers, totalgraphs)

    mobgraphRDD.groupBy(lambda x: x[2]).mapValues(lambda x: group_stat(x))\
        .saveAsTextFile(os.path.join(output, 'groupstat'))


if __name__ == '__main__':
    APP_NAME = "HZUserStat"
    conf = SparkConf().setAppName(APP_NAME)
    sc = SparkContext(conf=conf)
    thisdir = os.path.dirname(__file__)

    # add external python libraries
    xoxoZip = zippylib(os.path.join(thisdir, 'xoxo'))
    sc.addPyFile(xoxoZip)

    # Distribute map files onto cluster before running
    main(sc)
