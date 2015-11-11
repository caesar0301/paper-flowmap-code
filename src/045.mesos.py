#!/usr/bin/env python
# -*- encoding: utf-8
# Extract and analyze the movement motif.

from xoxo.roadnetwork import RoadNetwork
from xoxo.basestationmap import BaseStationMap
from xoxo.personmovday import movement_reader
from xoxo.settings import BSMAP, MOVEMENT_HIST, MAX_USER_NUM, HZ_SHAPEFILE

__author__ = 'Xiaming Chen'
__email__ = 'chen@xiaming.me'


def graph_node_sim(g1, g2):
    """ Implementation of similarity measure proposed by Blondel et al., 2004
    """
    pass

def graph_couple_sim(g1, g2):
    """ Implementation of node (edge) similarity measure of Zager et al., 2008
    """

if __name__ == '__main__':

    class IdCounter(object):
        ids = set()
        @staticmethod
        def count(new_id):
            IdCounter.ids.add(new_id)
            return len(IdCounter.ids)

    roadnet = RoadNetwork(HZ_SHAPEFILE)

    for person in movement_reader(MOVEMENT_HIST,
                                  BaseStationMap(BSMAP)):
        if IdCounter.count(person.id) > MAX_USER_NUM:
            break

        user_graph = person.convert2graph(roadnet, True)

        print user_graph.edge
