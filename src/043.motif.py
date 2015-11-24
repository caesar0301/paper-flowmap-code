#!/usr/bin/env python
# -*- encoding: utf-8
# Extract and analyze the movement motif.
import os

import networkx as nx
import numpy as np
import matplotlib.pyplot as plt
from pandas import DataFrame
from networkx.algorithms import isomorphism
from matplotlib.patches import FancyArrowPatch, Circle

from xoxo.bsmap import BaseStationMap
from xoxo.permov import movement_reader
from xoxo.utils import seq2graph
from xoxo.settings import BSMAP, MOVEMENT_HIST, MAX_USER_NUM

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

    def motif_iter(self, nnode=None):
        """Iterator over all motifs with specific number of nodes.

        Parameters
        ----------
        nnode: integer or list, optional
            If it is an integer, return motifs with the number of nodes.
            If it is a list of integer, return all motifs whose number falls
            into the list.
            If it is None, return all motifs without constraints.
        """
        if nnode is None:
            nnodes = self.all.keys()
        elif isinstance(nnode, int):
            nnodes = [nnode]
        elif isinstance(nnode, list):
            nnodes = nnode

        for nn in nnodes:
            motifs = self.all[nn]
            for ne in motifs.keys():
                motifs2 = motifs[ne]
                for motif in motifs2.keys():
                    yield (motif, motifs2[motif])

    def all_motifs(self, nnode=None, order_by_size=False, reverse=False):
        """Return a list of tuple (motif, count) with specifc number of nodes.
        """
        motifs = [i for i in self.motif_iter(nnode)]
        if order_by_size:
            motifs = sorted(motifs, key=lambda x: x[1], reverse=reverse)
        return motifs

    def number_of_motifs(self, nnode=None):
        """Return the number of motifs with specifc number of nodes.
        """
        counter = [cnt for motif, cnt in self.motif_iter(nnode)]
        return np.sum(counter)

    def stat(self):
        """Generate the stat of deteced motifs.
        """
        columns=['nnode', 'motifidx', 'count']
        result = DataFrame(columns=columns)
        for nn in self.all:
            motifs = self.all_motifs(nn, True)
            for i in range(len(motifs)):
                result = result.append(
                    DataFrame(np.array([[nn, i, motifs[i][1]]]), columns=columns),
                    ignore_index=True)

        return result


def draw_network(G, pos, ax):
    """ Draw network with curved edges.
    """
    for n in G:
        c = Circle(pos[n], radius=0.05, alpha=0.5)
        ax.add_patch(c)
        G.node[n]['patch'] = c
    seen={}
    for (u,v,d) in G.edges(data=True):
        n1 = G.node[u]['patch']
        n2 = G.node[v]['patch']
        rad = 0.1
        if (u,v) in seen:
            rad = seen.get((u,v))
            rad = (rad + np.sign(rad) * 0.1) * -1
        alpha = 0.5; color = 'k'
        e = FancyArrowPatch(n1.center, n2.center,
                            patchA=n1, patchB=n2,
                            arrowstyle='->',
                            connectionstyle='arc3,rad=%s' % rad,
                            mutation_scale=10.0,
                            lw=2, alpha=alpha, color=color)
        seen[(u, v)] = rad
        ax.add_patch(e)


if __name__ == '__main__':

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
    for person in movement_reader(movement, BaseStationMap(basemap)):

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

