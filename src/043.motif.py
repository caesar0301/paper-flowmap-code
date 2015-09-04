#!/usr/bin/env python
# -*- encoding: utf-8
# Extract and analyze the movement motif
# By Xiaming
import sys

import networkx as nx
import numpy as np
from pandas import DataFrame

from xoxo.utils import CellMapDB, movement_reader


class UserInfo(object):

    def __init__(self, **kwargs):
        self.data = dict(kwargs)


class Motif(object):
    """The repeated common parts in human mobility.
    See paper: C. Schneider, “Unravelling daily human mobility motifs,”
    Journal of the Royal Society, Interface / the Royal Society, 2013.
    """

    def __init__(self, n = None):
        self.all = {}
        self.n = n

    def add_graph(self, g, user_info):
        """Add a new graph to our motifs if it is new"""
        assert isinstance(g, nx.Graph)
        assert isinstance(user_info, UserInfo)

        c = len(g.nodes())
        if self.n is not None and c != self.n:
            return  # when it does not satisfy our target motif

        motifs = self.all
        nnode = len(g.nodes())
        if nnode not in motifs:
            motifs[nnode] = {g: [user_info]}
        else:
            preds = motifs[nnode].keys()
            found = False
            for ig in preds:
                if self.is_isomorphic(g, ig):
                    found = True
                    break
            if found:
                motifs[nnode][ig].append(user_info)
            else: # its a new motif
                motifs[nnode].update({g: [user_info]})

    def is_isomorphic(self, g1, g2):
        """Check if two graphs are isomorphic"""
        return nx.algorithms.isomorphism.is_isomorphic(g1, g2)

    def stat(self):
        """Generate the stat of deteced motifs"""
        columns=['nnode', 'motifidx', 'count']
        result = DataFrame(columns=columns)
        for nn in self.all:
            motifs = self.all[nn].values()
            motifs = sorted(motifs, key=lambda x: len(x), reverse=True)
            for i in range(0, len(motifs)):
                ## TODO: to inspect the topology of motif
                result = result.append(DataFrame(np.array([[nn, i, len(motifs[i])]]), columns=columns), ignore_index=True)
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
    edges = [i for i in zip(seq[0:N-2], seq[1:N-1]) if i[0] != i[1]]
    G.add_edges_from(edges)

    return G


##---------- Module Test -----------

class IdCounter(object):
    ids = set()
    @staticmethod
    def count(new_id):
        IdCounter.ids.add(new_id)
        return len(IdCounter.ids)

if __name__ == '__main__':
    import pickle

    if len(sys.argv) < 2:
        print("Usage: motifs.py <basemap> <movement>")
        sys.exit(-1)

    basemap = sys.argv[1]
    movement = sys.argv[2]

    CellMapDB(basemap)
    motifrepo = Motif()

    for person in movement_reader(movement):
        # if IdCounter.count(person.user_id) > 100:
        #     break
        # print('\n>>' + str(person))

        user_info = UserInfo(dow = person.dtstart.isoweekday(), uid = person.user_id)
        user_graph = seq2graph(person.locations, True)
        motifrepo.add_graph(user_graph, user_info)

    pickle.dump(motifrepo, open('motifs.pkl', 'wb'))
    motifrepo = pickle.load(open('motifs.pkl', 'rb'))
    motifrepo.stat().to_csv('motifs.csv', index=False)


