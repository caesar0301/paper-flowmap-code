import graphsim as gs
from munkres import Munkres
import networkx as nx
import numpy as np
from typedecorator import params


__author__ = 'Xiaming'


class Mesos(object):
    """ Extract mesostructure for two mobility graphs.
    """
    def __init__(self, G1, G2, nattr='weight', eattr='weight', lamb = 0.5):
        G1, G2 = sorted([G1, G2], key=lambda x: len(x))
        csim = gs.tacsim_combined(G1, G2, node_attribute=nattr, edge_attribute=eattr, lamb=lamb)
        print csim
        self.csim = csim / np.sqrt(((csim * csim).sum())) # to ensure valid structural distance
        print self.csim

        m = Munkres()
        cdist = (1 - self.csim).tolist()
        self.matching = m.compute(cdist)
        print self.matching

        nmap = {}
        def _gen_nnid(node):
            if node not in nmap:
                nmap[node] = len(nmap)
            return nmap[node]

        self.mesos = nx.DiGraph()
        for (e1_idx, e2_idx) in self.matching:
            e1 = G1.edges()[e1_idx]
            e2 = G2.edges()[e2_idx]
            ns = _gen_nnid(e1[0])
            nt = _gen_nnid(e1[1])
            self.mesos.add_edge(ns, nt)
            self.mesos.edge[ns][nt][eattr] = 0.5 * (G1.edge[e1[0]][e1[1]][eattr] + G2.edge[e2[0]][e2[1]][eattr])
            self.mesos.node[ns][nattr] = 0.5 * (G1.node[e1[0]][nattr] + G2.node[e2[0]][nattr])
            self.mesos.node[nt][nattr] = 0.5 * (G1.node[e1[1]][nattr] + G2.node[e2[1]][nattr])


    def struct_dist(self, eps=1e-3):
        ''' Structutal distance defined by a mesos for two mobility graphs.
        Refer to paper Mesos.
        '''
        sims = []
        for e1, e2 in self.matching:
            sims.append(self.csim[e1][e2])
        sims = np.array(sims)
        dist = np.sqrt(1 - np.dot(sims, sims))
        return (0 if dist <= eps else dist)


if __name__ == '__main__':
    G1 = nx.DiGraph()
    G1.add_weighted_edges_from([(1,0,8), (0,2,12), (1,2,10), (2,3,15)])
    G1.node[0]['weight'] = 1
    G1.node[1]['weight'] = 1
    G1.node[2]['weight'] = 5
    G1.node[3]['weight'] = 1

    G2 = nx.DiGraph()
    G2.add_weighted_edges_from([(0,1,15), (1,2,10)])
    G2.node[0]['weight'] = 1
    G2.node[1]['weight'] = 3
    G2.node[2]['weight'] = 1

    mesos = Mesos(G1, G2)

    print mesos.struct_dist()