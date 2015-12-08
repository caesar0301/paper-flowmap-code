#!/usr/bin/env python
# -*- encoding: utf-8 -*-
import sys, os

import numpy as np
import networkx as nx

from xoxo.bsmap import BaseStationMap
from xoxo.utils import greate_circle_distance
from xoxo.permov import movement_reader


__author__ = 'Xiaming Chen'
__email__ = 'chen@xiaming.me'


def load_oppmap(bsmap):
    """ Draw opportunity map from Flowmap
    """
    ifname = 'data/hcl_mesos0825_flowmap'


    last_interval = None
    graph = nx.Graph()
    nw = {}

    for line in open(ifname, 'rb'):
        interval, src, dst, total, unique = line.strip('\r\n').split(',')
        interval = int(interval)
        src = bsmap.get_coordinates(int(src))
        dst = bsmap.get_coordinates(int(dst))
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

    return graph


def opmap_stat():
    movdata = 'data/hcl_mesos0825'
    bsmap = 'data/hcl_mesos0825_bm'
    bsmap = BaseStationMap(bsmap)

    opgraph = load_oppmap(bsmap)
    opnodes = opgraph.nodes(data=True)

    for person in movement_reader(open(movdata, 'rb'), bsmap):
        if person.distinct_loc_num() < 2:
            continue

        rg = person.radius_of_gyration()
        alpha = 1
        delta = 0.05
        locs = person.coordinates
        home = person.coordinates[0]
        max_trd = np.max([greate_circle_distance(home[0], home[1], i[0], i[1]) for i in person.coordinates])

        for i in range(0, len(locs) - 1):
            j = i + 1
            dist = greate_circle_distance(locs[i][0], locs[i][1], locs[j][0], locs[j][1])

            # all opportunities for current location with radius rg
            person_opnodes = []
            for nn, vv in opnodes:
                if greate_circle_distance(nn[0], nn[1], locs[i][0], locs[i][1]) <= rg * alpha:
                    person_opnodes.append((nn, vv['weight']))

            aops = []
            iops = []

            for nn, value in person_opnodes:
                gcd = greate_circle_distance(locs[i][0], locs[i][1], nn[0], nn[1])
                if gcd < dist * (1 - delta):
                    iops.append((nn, value))
                elif gcd >= dist * (1 - delta) and gcd <= dist * (1 + delta):
                    aops.append((nn, value))

            print aops, iops

            avops_total = np.sum([p[1] for p in aops])
            avops_max = np.max([p[1] for p in aops])
            inops_total = np.sum([p[1] for p in iops])
            inops_max = np.max([p[1] for p in iops])

            print person.id, rg, avops_total, inops_total, avops_max, inops_max

        break


if __name__ == '__main__':
    print opmap_stat()