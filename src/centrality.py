#!/usr/bin/env python
# -*- encoding: utf-8 -*-
import pickle

import networkx as nx
import numpy as np
import matplotlib.pyplot as plt

from xoxo.utils import BaseStationMap, RoadNetwork, MobilityNetwork
from xoxo.utils import in_area, movement_reader
from xoxo.settings import BSMAP, MOVEMENT_HIST, MAX_USER_NUM, HZ_SHAPEFILE, HZ_LB, HZ_RT

__author__ = 'chenxm'


class IdCounter(object):
    ids = set()
    @staticmethod
    def count(new_id=None):
        if new_id is not None:
            IdCounter.ids.add(new_id)
        return len(IdCounter.ids)

# Road network
road_network = RoadNetwork(HZ_SHAPEFILE)

# Construct mobile network
bsmap = BaseStationMap(BSMAP)
# all_coordinates = bsmap.get_all_coordinates()
# hz_coordinates = [i for i in all_coordinates if in_area(i, HZ_LB, HZ_RT)]
#
# # mobile_network = MobilityNetwork(hz_coordinates, road_network)
# # pickle.dump(mobile_network, open('mobile_network.pkl', 'wb'))
# mobile_network = pickle.load(open('mobile_network.pkl', 'rb'))
#
# # Geodesic centrality
# print mobile_network.betweenness_centrality(1000)
# print mobile_network.edge_betweenness_centrality(1000)

# Empirical centrality
hedge_stat = {}
for person in movement_reader(MOVEMENT_HIST, bsmap):

    if IdCounter.count(person.user_id) > MAX_USER_NUM:
        break

    for i in set(person.coordinates):
        if i not in hedge_stat:
            hedge_stat[i] = 1
        else:
            hedge_stat[i] += 1
print hedge_stat

print IdCounter.count()


