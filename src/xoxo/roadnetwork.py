# Copyright (C) 2015, Xiaming Chen chen@xiaming.me
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
import json

import shapefile
import numpy as np
import networkx as nx
from matplotlib.patches import FancyArrowPatch, Circle


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
    """Draw network with curved edges.

    Examples
    --------

    plt.figure(figsize=(10, 10))
    ax=plt.gca()
    pos=nx.spring_layout(G)
    draw_network(G, pos, ax)
    ax.autoscale()
    plt.axis('equal')
    plt.axis('off')
    plt.title('Curved network')

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
                            arrowstyle='-|>',
                            connectionstyle='arc3,rad=%s' % rad,
                            mutation_scale=10.0,
                            lw=2, alpha=alpha, color=color)
        seen[(u, v)] = rad
        ax.add_patch(e)
    return e


def greate_circle_distance(lon0, lat0, lon1, lat1):
    """Return the distance (in km) between two points in
    geographical coordinates.
    """
    EARTH_R = 6372.8
    lat0 = np.radians(lat0)
    lon0 = np.radians(lon0)
    lat1 = np.radians(lat1)
    lon1 = np.radians(lon1)
    dlon = lon0 - lon1
    y = np.sqrt(
        (np.cos(lat1) * np.sin(dlon)) ** 2
        + (np.cos(lat0) * np.sin(lat1)
           - np.sin(lat0) * np.cos(lat1) * np.cos(dlon)) ** 2)
    x = np.sin(lat0) * np.sin(lat1) + \
        np.cos(lat0) * np.cos(lat1) * np.cos(dlon)
    c = np.arctan2(y, x)
    return EARTH_R * c


def shape2points(shpfile):
    """Extract point coordinats from a ERIS point shapefile.
    """
    sf = shapefile.Reader(shpfile)
    return [shape.points[0] for shape in sf.shapes()]


class RoadNetwork(object):
    """Convert an ERIS shapefile to an undirected graph weighted by distance.
    """

    def __init__(self, shapefile, edge_weighted_by_distance=True):
        g = nx.read_shp(shapefile)
        mg = max(nx.connected_component_subgraphs(g.to_undirected()), key=len)
        if edge_weighted_by_distance:
            for n0, n1 in mg.edges_iter():
                path = np.array(json.loads(mg[n0][n1]['Json'])['coordinates'])
                distance = np.sum(
                    greate_circle_distance(path[1:,0],path[1:,1], path[:-1,0], path[:-1,1])
                )
                mg.edge[n0][n1]['distance'] = distance
        self.graph = mg
        self._cache = {}
        self._cache_nn = {}

    def _hit_cache(self, lonlat1, lonlat2):
        hit = self._cache.get((lonlat1, lonlat2))
        if not hit:
            hit = self._cache.get((lonlat2, lonlat1))
        return hit

    def _update_cache(self, lonlat1, lonlat2, distance):
        self._cache.update({(lonlat1, lonlat2): distance})

    def _hit_cache_nn(self, lonlat):
        return self._cache_nn.get(lonlat)

    def _update_cache_nn(self, lonlat, nearest_node):
        self._cache_nn.update({lonlat: nearest_node})

    def nearest_node_to(self, lonlat):
        """ Find the nearest node of given point with (long, lat).
        """
        hit = self._hit_cache_nn(lonlat)
        if hit is not None:
            return hit
        nodes = np.array(self.graph.nodes())
        nn = np.argmin(np.sum((nodes[:,:] - lonlat)**2, axis=1))
        self._update_cache_nn(lonlat, nn)
        return self.graph.nodes()[nn]

    def shortest_path(self, lonlat1, lonlat2, weight='distance'):
        """Find the shortest path for a pair of points.
        Two points are not required to be the vertex of graph.
        """
        p1 = self.nearest_node_to(lonlat1)
        p2 = self.nearest_node_to(lonlat2)
        path = nx.shortest_path(self.graph, p1, p2, weight)
        return path

    def shortest_path_distance(self, lonlat1, lonlat2, weight='distance'):
        """Return the distance of two points with the shortest path algorithm.
        """
        hit = self._hit_cache(lonlat1, lonlat2)
        if hit is not None:
            return hit
        p1 = self.nearest_node_to(lonlat1)
        p2 = self.nearest_node_to(lonlat2)
        distance = nx.shortest_path_length(self.graph, p1, p2, weight)
        self._update_cache(lonlat1, lonlat2, distance)
        return distance
