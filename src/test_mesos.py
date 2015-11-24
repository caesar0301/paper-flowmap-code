import os
from xoxo.permov import movement_reader
from xoxo.bsmap import BaseStationMap
from xoxo.roadnet import RoadNetwork
from xoxo.settings import BSMAP, HZ_ROADNET

import graphsim as gs
import numpy as np

bsmap = BaseStationMap(BSMAP)
roadnet = RoadNetwork(HZ_ROADNET)

graphs = []
for person in movement_reader(os.path.join(os.path.dirname(__file__), '../data/hcl.sample'), bsmap):
    pgraph = person.convert2graph(roadnet)
    if len(pgraph) == 7:
        graphs.append(pgraph)

print graphs

for g1 in graphs:
    for g2 in graphs:
        G1 = g1
        G2 = g2
        G1, G2 = sorted([G1, G2], key=lambda x: len(x))
        csim = gs.tacsim_combined(G1, G2, node_attribute='dwelling', edge_attribute='distance')
        csim = csim / np.sqrt(((csim * csim).sum()))
        print csim