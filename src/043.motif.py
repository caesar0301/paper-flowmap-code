#!/usr/bin/env python
# -*- encoding: utf-8
# Extract and analyze the movement motif
# By Xiaming
import sys
import os

import networkx as nx
import numpy as np
from pandas import DataFrame
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, Circle

from xoxo.utils import CellMapDB, movement_reader


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

    def is_isomorphic(self, g1, g2):
        """Check if two graphs are isomorphic.
        To accelerate the process, we use an approximate algorithm,
        whose False value means definitely not isomorphic while True
        value does not guarantee isomorphic for 100%.
        """
        if g1.number_of_edges() != g2.number_of_edges():
            return False
        return nx.algorithms.isomorphism.faster_could_be_isomorphic(g1, g2)

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


def seq2graph(seq, directed=True):
    """Create a (weighted) directed graph from an odered
    sequence of items.
    """
    seq = [i for i in seq]
    N = len(seq)

    if directed:
        G = nx.DiGraph()
    else:
        G = nx.Graph()

    G.add_nodes_from(seq)
    edges = [i for i in zip(seq[0:N-1], seq[1:N]) if i[0] != i[1]]
    G.add_edges_from(edges)

    return G


def draw_network(G, pos, ax):
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
                            arrowstyle='-|>',
                            connectionstyle='arc3,rad=%s' % rad,
                            mutation_scale=10.0,
                            lw=2, alpha=alpha, color=color)
        seen[(u, v)] = rad
        ax.add_patch(e)
    return e


if __name__ == '__main__':

    class IdCounter(object):
        ids = set()
        @staticmethod
        def count(new_id):
            IdCounter.ids.add(new_id)
            return len(IdCounter.ids)

    if len(sys.argv) < 3:
        print("Usage: motifs.py <number> <basemap> <movement>")
        sys.exit(-1)

    counter = int(sys.argv[1])
    basemap = sys.argv[2]
    movement = sys.argv[3]

    CellMapDB(basemap)
    motifrepo = Motif()

    print("Extracting motifs ...")
    for person in movement_reader(movement):
        # for debugging
        if IdCounter.count(person.user_id) > counter:
            break

        user_graph = seq2graph(person.locations, True)
        motifrepo.add_graph(user_graph)

    motifrepo.stat().to_csv('motifs.csv', index=False)

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
