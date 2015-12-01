#!/usr/bin/env python
# -*- encoding: utf-8
# Extract and analyze the movement motif.
import os

import networkx as nx
import numpy as np
import matplotlib.pyplot as plt

from xoxo.bsmap import BaseStationMap
from xoxo.permov import movement_reader
from xoxo.utils import seq2graph, draw_network
from xoxo.settings import BSMAP, MOVEMENT_DAT, MAX_USER_NUM
from xoxo.motif import Motif

__author__ = 'Xiaming Chen'
__email__ = 'chen@xiaming.me'


if __name__ == '__main__':

    class IdCounter(object):
        ids = set()
        @staticmethod
        def count(new_id):
            IdCounter.ids.add(new_id)
            return len(IdCounter.ids)

    counter = MAX_USER_NUM
    basemap = BSMAP
    movement = MOVEMENT_DAT

    print("Extracting motifs ...")
    motifrepo = Motif()
    for person in movement_reader(open(movement, 'rb'), BaseStationMap(basemap)):

        if IdCounter.count(person.id) > counter:
            break

        user_graph = seq2graph(person.locations, True)
        motifrepo.add_graph(user_graph)

    motifrepo.stat().to_csv('motifs_stat.csv', index=False)

    print("Plotting motifs ...")
    motif_filter = range(3, 11)

    # Global stat
    all_motifs = motifrepo.all_motifs(motif_filter, True, True)
    totmotif = motifrepo.number_of_motifs(motif_filter)
    percs = [(motif, 1.0*count/totmotif) for (motif, count) in all_motifs]
    percs = [i for i in percs if i[1] >= 0.003]

    ncol = 5
    nrow = np.ceil(1.0 * len(percs) / ncol)

    plt.figure(figsize=(12, 20))
    for i in range(len(percs)):
        motif = percs[i][0]
        perc = percs[i][1]
        plt.subplot(nrow, ncol, i+1)
        ax=plt.gca()
        pos=nx.spring_layout(motif)
        draw_network(motif, pos, ax)
        ax.autoscale()
        plt.axis('equal')
        plt.axis('off')
        plt.title('%.1f%%, nn=%d' % (perc * 100, motif.number_of_nodes()))

    if not os.path.exists('motifs'):
        os.mkdir('motifs')
    plt.savefig('motifs/motif-all.pdf')

    # Stat by motif length
    for nn in motif_filter:
        total = motifrepo.number_of_motifs(nn)
        percs = [(motif, 1.0*count/total) for (motif, count) in motifrepo.motif_iter(nn)]
        percs = sorted(percs, key=lambda x: x[1], reverse=True)
        percs = [i for i in percs if i[1] >= 0.015]

        ncol = 5
        nrow = np.ceil(1.0 * len(percs) / ncol)

        # visualizing motifs
        plt.figure(figsize=(12, 12))
        for i in range(len(percs)):
            motif = percs[i][0]
            perc = percs[i][1]
            plt.subplot(nrow, ncol, i+1)
            ax=plt.gca()
            pos=nx.spring_layout(motif)
            draw_network(motif, pos, ax)
            ax.autoscale()
            plt.axis('equal')
            plt.axis('off')
            plt.title('%.1f%%' % (perc * 100))

        if not os.path.exists('motifs'):
            os.mkdir('motifs')
        plt.savefig('motifs/motif-%d.pdf' % nn)

