#!/usr/bin/env python
# -*- encoding: utf-8
__author__ = 'chenxm'

import numpy as np
from pandas import DataFrame
import networkx as nx
from networkx.algorithms import isomorphism


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