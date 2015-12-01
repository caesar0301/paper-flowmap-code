from datetime import datetime

import numpy as np
from typedecorator import params, returns

from roadnet import RoadNetwork
from bsmap import BaseStationMap
from settings import HZ_LB, HZ_RT
from utils import greate_circle_distance, seq2graph, drange, in_area


__all__ = ['movement_reader', 'PersonMoveDay']


def movement_reader(ifile, bsmap):
    """ An iterator to read personal daily data.
    """
    assert isinstance(bsmap, BaseStationMap)

    buf_ts = []
    buf_lc = []
    buf_cr = []
    last_uid = None
    last_day_start = None

    def check_time_alignment():
        if len(buf_ts) == 0:
            return False
        if buf_ts[-1] != buf_ts[0] + 86400:
            buf_ts.append(buf_ts[0] + 86400)
            buf_lc.append(buf_lc[0])
            buf_cr.append(buf_cr[0])
        return True

    for line in ifile:
        if isinstance(line, str):
            if line.startswith('#'):
                continue
            line = line.strip('\r\n ')
            uid, ts, loc = line.split(',')[0:3]
        elif isinstance(line, tuple):
            uid, ts, loc = line

        uid = int(uid)
        ts = int(float(ts))
        loc = int(loc)
        day_start, day_end = drange(ts)
        coord = bsmap.get_coordinates(loc)

        if not in_area(coord, HZ_LB, HZ_RT):
            continue

        if last_uid is None or uid == last_uid and day_start == last_day_start:
            buf_ts.append(ts)
            buf_lc.append(loc)
            buf_cr.append(coord)
        else:
            if check_time_alignment():
                yield PersonMoveDay(last_uid, last_day_start, buf_ts, buf_lc, buf_cr)

            buf_ts = [ts]
            buf_lc = [loc]
            buf_cr = [coord]

        last_uid = uid
        last_day_start = day_start

    if check_time_alignment():
        yield PersonMoveDay(last_uid, last_day_start, buf_ts, buf_lc, buf_cr)


def transtime(a, b):
    dist = greate_circle_distance(a[0], a[1], b[0], b[1])
    if dist <= 5: # km
        speed = 5
    elif dist <= 15:
        speed = 20
    else:
        speed = 30
    return 1.0 * dist / speed * 3600


class PersonMoveDay(object):
    """ An object to represent the daily mobility of individuals.

    The dewelling time at each location is controlled by
    :param dwelling_split_ratio: (default 0.8). With two timestamps at
    successive locations, the :param dwelling_split_ratio: * elapsed_duration
    contributes to the first location and the left to the second.
    """

    def __init__(self, user_id, dtstart, timestamps, locations, coordinates, dwelling_split_ratio=0.8):
        assert isinstance(dtstart, datetime)
        assert len(timestamps) == len(locations) == len(coordinates)

        self.id = user_id
        self.dtstart = dtstart
        self.dwelling = []
        self.accdwelling = {}   # accumulative dwelling time in secs

        # Remove duplicate records
        nodup = []
        last_location = None
        for i in range(len(locations)):
            if locations[i] != last_location:
                nodup.append(i)
            last_location = locations[i]

        self.timestamps = [timestamps[i] for i in nodup]    # timestamp sequence
        self.locations = [locations[i] for i in nodup]      # location sequence
        self.coordinates = [coordinates[i] for i in nodup]  # coordinate sequence
        self.circles = self._mine_circles(self.locations)

        # Calculate raw dwelling time
        last_timestamp = None
        last_location = None
        for i in range(len(locations)):
            if last_timestamp is None:
                last_timestamp = timestamps[i]
                self.dwelling.append(0)
            else:
                # Remove transmission slot
                delta = timestamps[i] - last_timestamp
                # Adjust dwelling time
                self.dwelling[-1] += int(delta * dwelling_split_ratio)
                split_left = int(delta * (1 - dwelling_split_ratio))
                if locations[i] != last_location:
                    self.dwelling.append(split_left)
                else:
                    self.dwelling[-1] += split_left
            last_location = locations[i]
            last_timestamp = timestamps[i]

        # Accumulative dwelling times
        for i in range(len(self.coordinates)):
            coord = self.coordinates[i]
            if coord not in self.accdwelling:
                self.accdwelling[coord] = 0
            self.accdwelling[coord] += self.dwelling[i]

        # Transition frequency
        self.freq = {}
        last_coord = None
        for coord in coordinates:
            if last_coord is None or coord == last_coord:
                last_coord = coord
                continue
            if (last_coord, coord) not in self.freq:
                self.freq[(last_coord, coord)] = 1
            else:
                self.freq[(last_coord, coord)] += 1
            last_coord = coord

    def __str__(self):
        return 'User %d: %s %d %s' % (
            self.id,
            self.dtstart.strftime('%Y%m%d'),
            len(self.circles),
            self.locations )

    def __len__(self):
        return len(self.locations)

    def is_strict_valid(self):
        pass

    def which_day(self):
        return self.dtstart.strftime("%m%d")

    @params(self=object, locs=[object])
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

    @params(self=object, road_network=RoadNetwork)
    def get_distances_from(self, road_network):
        """ Get geographical distances for each movement."""
        N = len(self.coordinates)
        distances = []
        for p1, p2 in zip(self.coordinates[0:N-1], self.coordinates[1, N]):
            distances.append(road_network.shortest_path_distance(p1, p2))
        return distances

    @params(self=object, road_network=RoadNetwork, directed=bool,
            edge_weighted_by_distance=bool, node_weighted_by_dwelling=bool)
    def convert2graph(self, road_network=None, directed=True,
                      edge_weighted_by_distance=True,
                      node_weighted_by_dwelling=True):
        """ Return a graph representation of human mobility, one which
        is weighted by traveling distance for edge and dwelling time for node.

        **PerfStat** (PersonNum,Calls,AccTime): 100,1519,54.191s
        """
        graph = seq2graph(self.coordinates, directed)

        if edge_weighted_by_distance:
            for edge in graph.edges_iter():
                if road_network:
                    dist = road_network.shortest_path_distance(edge[0], edge[1])
                else:
                    dist = greate_circle_distance(edge[0][0], edge[0][1], edge[1][0], edge[1][1])

                graph.edge[edge[0]][edge[1]]['weight'] = dist
                if edge in self.freq:
                    graph.edge[edge[0]][edge[1]]['frequency'] = self.freq[edge]
                else:
                    graph.edge[edge[0]][edge[1]]['frequency'] = 1

        if node_weighted_by_dwelling:
            for node in graph.nodes_iter():
                graph.node[node]['weight'] = self.accdwelling.get(node)

        return graph

    def radius_of_gyration(self):
        """ R_g based on edge distances
        """
        clon = np.average([coord[0] for coord in self.coordinates])
        clat = np.average([coord[1] for coord in self.coordinates])

        return np.average([greate_circle_distance(clon, clat, coord[0], coord[1]) for coord in self.coordinates])

    def travel_dist(self):
        """ Calculate the travelling distance totally.
        """
        if len(self.coordinates) < 2:
            return 0
        total = 0
        for i in range(0, len(self.coordinates)-1):
            lon1, lat1 = self.coordinates[i]
            lon2, lat2 = self.coordinates[i+1]
            total += greate_circle_distance(lon1, lat1, lon2, lat2)
        return total

    def distinct_loc_num(self):
        return len(set(self.locations))
