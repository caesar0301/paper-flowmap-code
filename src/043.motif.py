#!/usr/bin/env python
# -*- encoding: utf-8
# Extract and analyze the movement motif.
import os

import networkx as nx
import numpy as np
from pandas import DataFrame

from networkx.algorithms import isomorphism

__author__ = 'Xiaming Chen'
__email__ = 'chen@xiaming.me'


class Motif(object):
    """The repeated common parts in human mobility.
    See paper: C. Schneider, “Unravelling daily human mobility motifs,”
    Journal of the Royal Society, Interface / the Royal Society, 2013.
    """

    def __init__(self, n = None):
        self.all = {}
        self.n = n

    def add_graph(self, g):
        """Add a new graph to our motifs if it is new"""
        assert isinstance(g, nx.Graph)

        nnode = g.number_of_nodes()
        if self.n is not None and nnode != self.n:
            return  # when it does not satisfy our target motif

        motifs = self.all
        if nnode not in motifs:
            motifs[nnode] = {}

        nedge = g.number_of_edges()
        motifs2 = motifs[nnode]
        if nedge not in motifs2:
            motifs2[nedge] = {g: 1}
        else:
            # TODO: optimize the isomorphic searching
            preds = motifs2[nedge].keys()
            found = False
            for ig in preds:
                if self.is_isomorphic(g, ig):
                    found = True
                    break
            if found:
                motifs2[nedge][ig] += 1
            else: # its a new motif
                motifs2[nedge].update({g: 1})

    def is_isomorphic(self, g1, g2, approximate=False):
        """Check if two graphs are isomorphic.
        To accelerate the process, we use an approximate algorithm,
        whose False value means definitely not isomorphic while True
        value does not guarantee isomorphic for 100%.
        """
        if approximate:
            return isomorphism.faster_could_be_isomorphic(g1, g2)
        else:
            if isomorphism.faster_could_be_isomorphic(g1, g2):
                if isomorphism.is_isomorphic(g1, g2):
                    return True
            return False

    def motif_iter(self, nnode):
        """Iterator over all motifs with specific number of nodes."""
        motifs = self.all[nnode]
        for nedge in motifs.keys():
            motifs2 = motifs[nedge]
            for motif in motifs2.keys():
                yield (motif, motifs2[motif])

    def all_motifs(self, nnode, order_by_size=False):
        motifs = [i for i in self.motif_iter(nnode)]
        if order_by_size:
            motifs = sorted(motifs, key=lambda x: x[1], reverse=True)
        return motifs

    def number_of_motifs(self, nnode):
        """Return the number of motifs with specifc number of nodes."""
        motifs = self.all[nnode]
        counter = [motifs[nedge][motif] for nedge in motifs for motif in motifs[nedge]]
        return np.sum(counter)

    def stat(self):
        """Generate the stat of deteced motifs."""
        columns=['nnode', 'motifidx', 'count']
        result = DataFrame(columns=columns)
        for nn in self.all:
            motifs = self.all_motifs(nn, True)
            for i in range(len(motifs)):
                result = result.append(DataFrame(np.array([[nn, i, motifs[i][1]]]), columns=columns), ignore_index=True)

        return result


if __name__ == '__main__':
    import matplotlib.pyplot as plt

    from xoxo.utils import CellMapDB, movement_reader, seq2graph, draw_network
    from xoxo.settings import BSMAP, MOVEMENT_HIST, MAX_USER_NUM

    class IdCounter(object):
        ids = set()
        @staticmethod
        def count(new_id):
            IdCounter.ids.add(new_id)
            return len(IdCounter.ids)

    counter = MAX_USER_NUM
    basemap = BSMAP
    movement = MOVEMENT_HIST

    print("Extracting motifs ...")
    motifrepo = Motif()
    for person in movement_reader(movement, CellMapDB(basemap)):

        if IdCounter.count(person.user_id) > counter:
            break

        user_graph = seq2graph(person.locations, True)
        motifrepo.add_graph(user_graph)

    motifrepo.stat().to_csv('motifs_stat.csv', index=False)

    print("Plotting motifs ...")
    for n in motifrepo.all.keys():
        if n < 3 or n > 10:
            continue
        motifs = motifrepo.all[n].keys()
        total = motifrepo.number_of_motifs(n)
        percs = [(motif, 1.0*count/total) for (motif, count) in motifrepo.motif_iter(n)]
        percs = sorted(percs, key=lambda x: x[1], reverse=True)
        percs = [i for i in percs if i[1] >= 0.015]

        ncol = 5
        nrow = np.ceil(1.0 * len(percs) / ncol)

        # visualizing motifs
        plt.figure(figsize=(15, 15))
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
        plt.savefig('motifs/motif-%d.pdf' % n)
