import networkx as nx
from typedecorator import params, returns

from roadnet import RoadNetwork


class Hyperedge(object):

    def __init__(self, v=None):
        self._vertices = []
        if isinstance(v, tuple) and isinstance(v[0], float):
            self.add_vertex(v)
        elif isinstance(v, list) and isinstance(v[0], tuple):
            [self.add_vertex(i) for i in v]
        elif isinstance(v, tuple) and isinstance(v[0], tuple):
            [self.add_vertex(i) for i in v]

    @params(self=object, v=(float, float))
    def add_vertex(self, v):
        self._vertices.append(v)
        self._vertices.sort()

    @params(self=object, n=int)
    def get_vertices(self, n=None):
        if n is not None:
            return self._vertices[0:n]
        return tuple(self._vertices)

    @params(self=object, v=(float, float))
    def has_vertex(self, v):
        return v in self._vertices

    def extend(self, other):
        self._vertices.extend(other._vertices)
        self._vertices.sort()

    def __len__(self):
        return self._vertices.__len__()

    def __str__(self):
        return str(tuple(self._vertices))

    def __hash__(self):
        return tuple(self._vertices).__hash__()

    def __cmp__(self, other):
        return other._vertices == self._vertices


class MobilityNetwork(object):

    @params(self=object, coordinates=[(float, float)], roadnet=RoadNetwork)
    def __init__(self, coordinates, roadnet):
        """
        Mapping coordinates of mobile networks onto road network.
        Thus mere the static distance information is considered in analyzing
        the mobile network properties.

        Parameters
        ----------

        coordinates : list of 2-tuple
          A list of geographic coordinates defining the locations of
          mobile base stations.

        roadnet : instance of :class: RoadNetwork
          A static road network constructed from Eris shape file.

        """
        self.graph = roadnet.graph
        self.coordinates = coordinates

        # Coordinates > RoadPoint
        self.coordmap = {}
        for i in self.coordinates:
            self.coordmap[i] = roadnet.nearest_node_to(i)

        # RoadPoint > Hyperedge
        self.coordmapr = {}
        for coord, rnode in self.coordmap.items():
            if rnode not in self.coordmapr:
                self.coordmapr[rnode] = Hyperedge(coord)
            else:
                self.coordmapr[rnode].extend(Hyperedge(coord))

    @params(with_road_vertices=bool)
    def get_hyperedges(self, with_road_vertices=False):
        """ Get the hyperedges of mapped mobile network. We map each coordinates
        to the nearest road vertex and multiple coordinates mapped to the same vertex
        constitute a hyperedge. People at the hyperedge are assumed to connect inner
        base stations with equal probabilities.
        """
        if not with_road_vertices:
            return self.coordmapr.values()
        hyperedges = {}
        for rnode, hedge in self.coordmapr.items():
            hyperedges[hedge] = rnode
        return hyperedges

    @params(self=object, source=(float, float), target=(float, float))
    def shortest_path(self, source, target):
        """
        Get the shortest path segments for a pair of coordinates in mobile networks.

        Returns
        -------

        Shortest path : list
          List of elements of Hyperedge if the path vertex is as mobile
          base station and road network point (2-tuple) otherwise.

        """
        road_source = self.coordmap[source]
        road_target = self.coordmap[target]
        road_sp = nx.shortest_path(self.graph, road_source, road_target, weight='distance')
        return [self.coordmapr.get(p, p) for p in road_sp]

    @params(self=object, source=(float, float), target=(float, float))
    def shortest_path_length(self, source, target):
        """ Get the shortest path length for a pair of coordinates
            in mobile networks.
        """
        road_source = self.coordmap[source]
        road_target = self.coordmap[target]
        return nx.shortest_path_length(self.graph, road_source, road_target, weight='distance')

    @params(k=int)
    @returns({Hyperedge: float})
    def betweenness_centrality(self, k=None):
        """ Calculate the betweenness centrality of each coordinates or hyperedge
            in mobile network. The algorithm uses edge weight with `distance`.
        """
        road_bw = nx.betweenness_centrality(self.graph, k=k, weight='distance')
        mobile_bw = {}
        for rnode, hedge in self.coordmapr.items():
            mobile_bw[hedge] = road_bw[rnode]
        return mobile_bw

    @params(k=int)
    @returns({(Hyperedge, Hyperedge): float})
    def edge_betweenness_centrality(self, k=None):
        """ Calculate the edge betweenness centrality of each pair of hyperedges
            in mobile network. The algorithm uses `distance` to weight each segment.
        """
        road_bw = nx.edge_betweenness_centrality(self.graph, k=k, weight='distance')
        mobile_bw = {}
        for (source, target), betweenness in road_bw.items():
            if source in self.coordmapr and target in self.coordmapr:
                mobile_bw[(self.coordmapr[source], self.coordmapr[target])] = betweenness
        return mobile_bw
