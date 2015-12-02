#!/usr/bin/env python
# -*- encoding: utf-8 -*-
import os

import numpy as np
import networkx as nx
import matplotlib.pyplot as plt
from networkx.drawing.nx_pylab import draw_networkx

from xoxo.bsmap import BaseStationMap
from xoxo.permov import movement_reader
from xoxo.mesos import Mesos
from networkx.algorithms import isomorphism
from xoxo.utils import dumps_mobgraph, loads_mobgraph, draw_network

__author__ = 'Xiaming Chen'
__email__ = 'chen@xiaming.me'


def top_compare():
    """ Compare top motif and mesostructure
    """
    datapath = 'data/mesos0822_s0dot2'
    movdata = 'data/hcl_mesos0822_sample0.2'
    bsmap = 'data/hcl_mesos0822_bm'
    ofname = os.path.join(datapath, 'mesos0822_s0dot2_top')

    mobgraphs = {}
    for person in movement_reader(open(movdata), BaseStationMap(bsmap)):
        if person.which_day() != '0822':
            continue

        nn = len(set(person.locations))
        if nn > 20:
            continue
        if nn not in mobgraphs:
            mobgraphs[nn] = {}

        mobgraphs[nn][person.id] = person.convert2graph()

    new_file = True
    for C in range(3, 16):
        for kn in range(1, 5):

            print C, kn

            # Read dist matrix for (group, cluster) users
            fileklab = os.path.join(datapath, 'mesos0822_s0dot2_c%d_kn%d' % (C, kn))
            distmat = []
            i = 0
            for line in open(fileklab):
                if i == 0:
                    uids = [ int(i) for i in line.strip('\r\n').split(',') ]
                    i == 1
                    continue
                distmat.append([float(i) for i in line.strip('\r\n').split(',')])

            distmat = np.array(distmat)
            distvec = distmat.sum(1) / len(uids)
            uids_sorted = [x for (y, x) in sorted(zip(distvec, uids))]

            N = len(uids_sorted)
            print('Total users %d: ' % N)

            mgs = mobgraphs[C]
            mesos = Mesos(mgs[uids_sorted[0]], mgs[uids_sorted[1]])
            topmesos = mesos.mesos
            topmesos_sim = 1 - mesos.struct_dist()

            motifs = {}
            for i in range(N-1):
                u1 = uids_sorted[i]
                u2 = uids_sorted[i+1]
                g1 = mgs[u1]
                g2 = mgs[u2]
                mesos = Mesos(g1, g2).mesos
                found = False
                for key in motifs.keys():
                    if isomorphism.is_isomorphic(key, mesos):
                        motifs[key].append((mesos, i))
                        found = True
                    if found:
                        break
                if not found:
                    motifs[mesos] = [(mesos, i)]

            res = []
            for key, value in motifs.items():
                res.append((len(value), value[0][0]))
            res = sorted(res, key=lambda x: x[0], reverse=True)
            topmotif = res[0][1]
            topmotif_supp = 1.0 * res[0][0] / N

            if new_file:
                mode = 'wb'
                new_file = False
            else:
                mode = 'ab'
            ofile = open(ofname, mode)

            ofile.write('%d\t%d' % (C, kn))
            ofile.write('\t%.3f\t%.3f' % (topmesos_sim, topmotif_supp))
            ofile.write('\t%s' % dumps_mobgraph(topmesos))
            ofile.write('\t%s' % dumps_mobgraph(topmotif))
            ofile.write('\n')
            ofile.close()


def trv_distance():
    """ Travel distance for clustered users
    """
    datapath = 'data/mesos0822_s0dot2'
    movdata = 'data/hcl_mesos0822_sample0.2'
    bsmap = 'data/hcl_mesos0822_bm'
    ofname = os.path.join(datapath, 'mesos0822_s0dot2_trd')

    travdist = {}
    mobgraphs = {}
    for person in movement_reader(open(movdata), BaseStationMap(bsmap)):
        if person.which_day() != '0822':
            continue

        nn = len(set(person.locations))
        if nn > 20:
            continue
        if nn not in mobgraphs:
            mobgraphs[nn] = {}

        mobgraphs[nn][person.id] = person.convert2graph()

        circle_num = len(person.circles)
        edge_freq = np.mean(person.freq.values())
        trvd = person.travel_dist()
        rg = person.radius_of_gyration()
        nloc = len(person.locations)
        travdist[person.id] = (rg, trvd, edge_freq, circle_num, nloc)

    new_file = True
    for C in range(2, 16):
        for kn in range(1, 5):

            print C, kn

            # Read dist matrix for (group, cluster) users
            fileklab = os.path.join(datapath, 'mesos0822_s0dot2_c%d_kn%d' % (C, kn))
            distmat = []
            i = 0
            for line in open(fileklab):
                if i == 0:
                    uids = [ int(i) for i in line.strip('\r\n').split(',') ]
                    i == 1
                    continue
                distmat.append([float(i) for i in line.strip('\r\n').split(',')])

            distmat = np.array(distmat)
            distvec = distmat.sum(1) / len(uids)
            uids_sorted = [x for (y, x) in sorted(zip(distvec, uids))]

            N = len(uids_sorted)
            print('Total users %d: ' % N)

            mgs = mobgraphs[C]
            mesos = Mesos(mgs[uids_sorted[0]], mgs[uids_sorted[1]])
            topmesos = mesos.mesos
            eigndist = np.sum([e[2]['distance'] for e in topmesos.edges(data=True)])

            if new_file:
                mode = 'wb'
                new_file = False
            else:
                mode = 'ab'
            ofile = open(ofname, mode)
            if mode == 'wb':
                ofile.write('uid,group,clust,eigndist,rg,trvd,efreq,circlenum,nloc,dist,selfdist\n')

            for i in range(0, len(uids)):
                uid = uids_sorted[i]
                dist = np.sum(distmat[i]) / len(uids)
                selfdist = distmat[i][i]
                rg, trvd, edge_freq, circle_num, nloc = travdist[uid]
                ofile.write('%d,%d,%d,%.3f,%.3f,%.3f,%.3f,%d,%d,%.3f,%.3f' % \
                            (uid, C, kn, eigndist, rg, trvd, edge_freq, circle_num, nloc, dist, selfdist))
                ofile.write('\n')

            ofile.close()


def draw_top_compare():
    """ Plot results of top_compare
    """

    ifname = 'data/mesos0822_s0dot2/mesos0822_s0dot2_stat'

    res = []
    for line in open(ifname):
        group, kn, mesos_sim, motif_supp, mesos, motif = line.strip('\r\n').split('\t')

        mesos = loads_mobgraph(mesos)
        motif = loads_mobgraph(motif)
        res.append((int(group), int(kn), float(mesos_sim), float(motif_supp), mesos, motif))

    ncol = 5
    nrow = np.ceil(1.0 * len(res) / ncol)

    plt.figure(figsize=(20, 40))
    for i in range(len(res)):
        motif = res[i][5]
        supp = res[i][3]
        plt.subplot(nrow, ncol, i+1)
        draw_networkx(motif)
        plt.title('%.1f%%, nn=%d' % (supp * 100, motif.number_of_nodes()))

    plt.savefig('figures/mesos0822_s0.2_top_motif.pdf')




if __name__ == '__main__':
    top_compare()