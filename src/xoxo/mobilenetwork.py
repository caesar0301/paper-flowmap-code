import networkx as nx
from typedecorator import params

from roadnetwork import RoadNetwork


class MobilityNetwork(object):

    @params(self=object, coordinates=[(float, float)], roadnet=RoadNetwork)
    def __init__(self, coordinates, roadnet):
        self.graph = roadnet.graph
        self.coordinates = coordinates

        self.coordmap = {}
        for coord in self.coordinates:
            self.coordmap[coord] = roadnet.nearest_node_to(coord)

        self.coordmapr = {}
        for coord in self.coordmap:
            nn = self.coordmap[coord]
            if nn not in self.coordmapr:
                self.coordmapr[nn] = []
            self.coordmapr[nn].append(coord)

    @params(self=object, source=(float, float), target=(float, float))
    def shortest_path(self, source, target):
        assert source in self.coordmap and target in self.coordmap

        road_source = self.coordmap[source]
        road_target = self.coordmap[target]
        road_sp = nx.shortest_path(self.graph, road_source, road_target, weight='distance')

        return [self.coordmapr[p] if p in self.coordmapr else [p] for p in road_sp]

    @params(self=object, source=(float, float), target=(float, float))
    def shortest_path_length(self, source, target):
        assert source in self.coordmap and target in self.coordmap

        road_source = self.coordmap[source]
        road_target = self.coordmap[target]

        return nx.shortest_path_length(self.graph, road_source, road_target, weight='distance')
