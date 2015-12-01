#!/usr/bin/env python
# -*- encoding: utf-8 -*-
import sys, os

import numpy as np
import networkx as nx

from xoxo.bsmap import BaseStationMap
from xoxo.utils import greate_circle_distance


__author__ = 'Xiaming Chen'
__email__ = 'chen@xiaming.me'


def read_dt_model():
    ifname = 'data/hcl_mesos7d_dtloc_log_model_clean'

    models = []
    i = 0
    for line in open(ifname, 'rb'):
        if i == 0:
            i = 1
            continue

        uid, mu1 ,mu2, sigma1, sigma2, lamb = line.strip('\r\n').split(',')
        models.append((float(mu1), float(mu2), float(sigma1), float(sigma2), float(lamb)))

    return models


def load_oppmap():
    """ Draw opportunity map from Flowmap
    """
    ifname = 'data/hcl_mesos0825_flowmap'
    ofname = 'data/hcl_mesos0825_oppmap'


    last_interval = None
    graph = nx.Graph()
    nw = {}

    for line in open(ifname, 'rb'):
        interval, src, dst, total, unique = line.strip('\r\n').split(',')
        interval = int(interval)
        src = int(src)
        dst = int(dst)
        total = int(total)
        unique = int(unique)

        # if last_interval and interval != last_interval:
        #     break

        if dst not in nw:
            nw[dst] = unique
        else:
            nw[dst] += unique

        graph.add_edge(src, dst)

        last_interval = interval

    for nid in graph.nodes():
        if nid in nw:
            graph.node[nid]['weight'] = nw[nid]
        else:
            graph.node[nid]['weight'] = 0

    # dump oppmap
    ofile = open(ofname, 'wb')
    ofile.write('bsid,unique\n')

    for node in graph.nodes(data=True):
        ofile.write('%d,%d\n' % (node[0], node[1]['weight']))
    ofile.close()

    return graph


def random_lmnorm(mu1, mu2, sigma1, sigma2, lamb):
    """ Generate random number for log-normal mixture model
    """
    while True:
        a = np.random.lognormal(mu1, sigma1)
        b = np.random.lognormal(mu2, sigma2)
        c = lamb * a + (1-lamb) * b

        if c < 86400 and c > 100:
            return c


def personal_map(rg, graph, bsmap, expasion=1.2):
    """ Generate individual's map
    """
    locs = [(i[0], i[1]['weight'])for i in graph.nodes(data=True)]
    randhome = locs[np.random.random_integers(len(locs))]
    mymap = []
    for loc in locs:
        s = bsmap.get_coordinates(randhome[0])
        d = bsmap.get_coordinates(loc[0])
        dist = greate_circle_distance(s[0], s[1], d[0], d[1])

        if dist <= rg * expasion:
            mymap.append(loc)

    return (randhome, mymap)


def random_strategy(curloc, personmap):
    return personmap[np.random.random_integers(len(personmap))]


def simulate(N = 5):
    bsmap = BaseStationMap('data/hcl_mesos0825_bm')
    dtmodel = read_dt_model()
    nmodel = len(dtmodel)
    oppmap = load_oppmap()

    TIMEBOUND = 86400 - 3600 * 6

    for i in range(1, 100):
        # generate random user
        uid = np.random.random_integers(nmodel)
        dtm = dtmodel[uid]
        myhome, mymap = personal_map(5, oppmap, bsmap)

        acctime = 0
        curloc = myhome
        locstat = {myhome: 0}
        locseq = []
        while acctime < TIMEBOUND:
            nextloc = random_strategy(curloc, mymap)
            dt = random_lmnorm(dtm[0], dtm[1], dtm[2], dtm[3], dtm[4])

            if acctime + dt > TIMEBOUND:
                locstat[myhome] += (TIMEBOUND - acctime)
                break

            if len(locstat) == N:
                locstat[myhome] += (TIMEBOUND - acctime)
                break

            if curloc not in locstat:
                locstat[curloc] = dt
            else:
                locstat[curloc] += dt
            acctime += dt

            locseq.append(curloc)
            curloc = nextloc

        if len(locstat) == N:
            dist = []
            for i in range(1, len(locseq)):
                s = bsmap.get_coordinates(locseq[i-1][0])
                d = bsmap.get_coordinates(locseq[i][0])
                dist.append(greate_circle_distance(s[0], s[1], d[0], d[1]))

            print dist

            print locstat


if __name__ == '__main__':
    simulate()