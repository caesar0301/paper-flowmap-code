#!/usr/bin/env python
# Read the movement history and mobile network topology
# By mxc
import sys
import json
from datetime import datetime

import shapefile
import numpy as np
import networkx as nx
from matplotlib.patches import FancyArrowPatch, Circle


class CellMapDB(object):
    """ A singleton to store mobile network topology
    """
    _instance = None
    _mapDB = {}

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(CellMapDB, cls).__new__(cls, *args, **kwargs)
        return cls._instance

    def __init__(self, path=None):
        if path:
            self.load_database(path)

    def load_database(self, path):
        print("Loading cell map database ...")
        for line in open(path, 'rb'):
            parts = line.strip('\r\n ').split(',')
            id = int(parts[0])
            lon = float(parts[2])
            lat = float(parts[3])
            self._mapDB[id] = (lon, lat)

    def validate_database(self):
        if len(self._mapDB) == 0:
            print("ERROR: the map DB is not initialized, exiting")
            sys.exit(1)

    def get_coordinates(self, id):
        self.validate_database()
        return self._mapDB[id]

    def get_coordinates_from(self, ids):
        self.validate_database()
        return [self._mapDB[i] for i in ids]


def drange(ts):
    """ Determine the range of a valid day now with
    (03:00 ~ 03:00 next day)
    """
    dt = datetime.fromtimestamp(ts)
    if dt.hour < 3:
        sds = datetime(dt.year, dt.month, dt.day-1, 3)
    else:
        sds = datetime(dt.year, dt.month, dt.day, 3)
    eds = sds.replace(day=sds.day+1)
    return (sds, eds)


def is_valid_location(location_id, bsmap):
    """ Check if given location point is valid
    """
    HZ_LB = [120.03013, 30.13614]
    HZ_RT = [120.28597, 30.35318]
    coord = bsmap.get_coordinates(location_id)
    lon = coord[0]
    lat = coord[1]
    return in_area([lon, lat], HZ_LB, HZ_RT)


def in_area(p, lb, rt):
    """Check if a point (lon, lat) is in an area denoted by
    the left-below and right-top points.
    """
    if p[0] >= lb[0] and p[0] <= rt[0] and p[1] >= lb[1] and p[1] <= rt[1]:
        return True
    return False


class PersonMoveDay(object):

    def __init__(self, user_id, dtstart, timestamps, locations, coordinates):
        assert isinstance(dtstart, datetime)
        assert isinstance(timestamps, list)
        assert isinstance(locations, list)

        self.user_id = user_id
        self.dtstart = dtstart

        # Remove duplicate stays
        nodup = []
        last = None
        for i in range(0, len(locations)):
            if locations[i] != last:
                nodup.append(i)
            last = locations[i]

        self.timestamps = [timestamps[i] for i in nodup]
        self.locations = [locations[i] for i in nodup]
        self.circles = self._mine_circles(self.locations)
        self.coordinates = [coordinates[i] for i in nodup]
        self.dwelling = None

    def __str__(self):
        return 'User %d: %s %d %s' % (
            self.user_id,
            self.dtstart.strftime('%Y%m%d'),
            len(self.circles),
            self.locations
        )

    def _mine_circles(self, locs):
        """ Extract movement circles from a location sequence
        """
        i = 0; n = len(locs)
        circles = []
        while i < n:
            found = False
            for j  in range(i+1, n):
                if locs[j] == locs[i]:
                    found = True
                    circles.append((i, j))
                    deeper = self._mine_circles(locs[i+1:j])
                    deeper = [(t[0]+i+1, t[1]+i+1) for t in deeper]
                    circles.extend(deeper)
                    break
            i = j if found else (i + 1)
        return circles

    def get_distances_from(self, road_network):
        """ Get geographical distances for each movement."""
        assert isinstance(road_network, RoadNetwork)
        N = len(self.coordinates)
        distances = []
        for p1, p2 in zip(self.coordinates[0:N-1], self.coordinates[1, N]):
            distances.append(road_network.shortest_path_distance(p1, p2))
        return distances

    def convert2graph(self, road_network, directed=True,
                      edge_weighted_by_distance=True,
                      node_weighted_by_dwelling_time=True):
        """ Return a graph representation of human mobility, one which
        is weighted by traveling distance at edge and dwelling time at node.

        @PerfStat (PersonNum,Calls,AccTime):
            100,1519,54.191s
        """
        graph = seq2graph(self.coordinates, directed)

        if edge_weighted_by_distance:
            for edge in graph.edges_iter():
                graph.edge[edge[0]][edge[1]]['distance'] = \
                    road_network.shortest_path_distance(edge[0], edge[1])

        if node_weighted_by_dwelling_time:
            for node in graph.nodes_iter():
                graph.node[node]['dwelling_time'] = (node in self.coordinates)

        return graph


def movement_reader(fname, bsmap):
    """ An iterator to read personal daily data.
    """
    buf_ts = []
    buf_lc = []
    buf_cr = []
    last_uid = None
    last_day_start = None

    def check_time_alignment():
        if buf_ts[-1] != buf_ts[0] + 86400:
            buf_ts.append(buf_ts[0] + 86400)
            buf_lc.append(buf_lc[0])
            buf_cr.append(buf_cr[0])

    for line in open(fname, 'rb'):
        line = line.strip('\r\n ')

        if line.startswith('#'): continue

        uid, ts, loc = line.split(',')[0:3]
        uid = int(uid)
        ts = int(float(ts))
        loc = int(loc)
        coord = bsmap.get_coordinates(loc)
        day_start, day_end = drange(ts)

        if not is_valid_location(loc, bsmap):
            continue

        if last_uid is None or uid == last_uid and day_start == last_day_start:
            buf_ts.append(ts)
            buf_lc.append(loc)
            buf_cr.append(coord)
        else:
            check_time_alignment()
            yield PersonMoveDay(last_uid, last_day_start, buf_ts, buf_lc, buf_cr)

            buf_ts = [ts]
            buf_lc = [loc]
            buf_cr = [coord]

        last_uid = uid
        last_day_start = day_start

    check_time_alignment()
    yield PersonMoveDay(last_uid, last_day_start, buf_ts, buf_lc, buf_cr)


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
    """ Draw network with curved edges.

    Example
    -------

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
        print("Reading road network ...")
        g = nx.read_shp(shapefile)
        mg = max(nx.connected_component_subgraphs(g.to_undirected()), key=len)
        if edge_weighted_by_distance:
            for n0, n1 in mg.edges_iter():
                path = np.array(json.loads(mg[n0][n1]['Json'])['coordinates'])
                distance = np.sum(
                    greate_circle_distance(path[1:,0],path[1:,1], path[:-1,0], path[:-1,1])
                )
                mg.edge[n0][n1]['distance'] = distance
        self.G = mg
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
        nodes = np.array(self.G.nodes())
        nn = np.argmin(np.sum((nodes[:,:] - lonlat)**2, axis=1))
        self._update_cache_nn(lonlat, nn)
        return nn

    def shortest_path(self, lonlat1, lonlat2, weight='distance'):
        """Find the shortest path for a pair of points.
        Two points are not required to be the vertex of graph.
        """
        nodes = np.array(self.G.nodes())
        p1 = self.nearest_node_to(lonlat1)
        p2 = self.nearest_node_to(lonlat2)
        path = nx.shortest_path(self.G, tuple(nodes[p1]), tuple(nodes[p2]), weight)
        return path

    def shortest_path_distance(self, lonlat1, lonlat2, weight='distance'):
        """Return the distance of two points with the shortest path algorithm.
        """
        hit = self._hit_cache(lonlat1, lonlat2)
        if hit is not None:
            return hit
        sp = self.shortest_path(lonlat1, lonlat2, weight)
        distances = [self.G.edge[sp[i]][sp[i+1]][weight] for i in range(len(sp)-1)]
        distance = np.sum(distances)
        self._update_cache(lonlat1, lonlat2, distance)
        return distance

