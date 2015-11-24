from datetime import datetime

from typedecorator import params, returns

from roadnet import RoadNetwork
from bsmap import BaseStationMap
from settings import HZ_LB, HZ_RT
from utils import greate_circle_distance, seq2graph, drange, in_area


__all__ = ['movement_reader', 'movement_extractor', 'PersonMoveDay']


@params(fname=str, bsmap=BaseStationMap)
def movement_reader(fname, bsmap):
    """ An iterator to read personal daily data.
    """
    assert isinstance(bsmap, BaseStationMap)

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
        day_start, day_end = drange(ts)
        coord = bsmap.get_coordinates(loc)

        if not in_area(coord, HZ_LB, HZ_RT):
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


@returns(list)
@params(records=list, bsmap=BaseStationMap)
def movement_extractor(records, bsmap):
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

    person_daily_movs = []
    for uid, ts, loc in records:
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
                person_daily_movs.append(PersonMoveDay(last_uid, last_day_start,
                                                       buf_ts, buf_lc, buf_cr))

            buf_ts = [ts]
            buf_lc = [loc]
            buf_cr = [coord]

        last_uid = uid
        last_day_start = day_start

    if check_time_alignment():
        person_daily_movs.append(PersonMoveDay(last_uid, last_day_start,
                                                buf_ts, buf_lc, buf_cr))
    return person_daily_movs


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
        self.accdwelling = {}

        # Remove duplicate records
        nodup = []
        last_location = None
        for i in range(len(locations)):
            if locations[i] != last_location:
                nodup.append(i)
            last_location = locations[i]

        self.timestamps = [timestamps[i] for i in nodup]
        self.locations = [locations[i] for i in nodup]
        self.circles = self._mine_circles(self.locations)
        self.coordinates = [coordinates[i] for i in nodup]

        def transtime(a, b):
            dist = greate_circle_distance(a[0], a[1], b[0], b[1])
            if dist <= 5: # km
                speed = 5
            elif dist <= 15:
                speed = 20
            else:
                speed = 30
            return 1.0 * dist / speed * 3600

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

    def __str__(self):
        return 'User %d: %s %d %s' % (
            self.id,
            self.dtstart.strftime('%Y%m%d'),
            len(self.circles),
            self.locations
        )

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
    def convert2graph(self, road_network, directed=True,
                      edge_weighted_by_distance=True,
                      node_weighted_by_dwelling=True):
        """ Return a graph representation of human mobility, one which
        is weighted by traveling distance for edge and dwelling time for node.

        **PerfStat** (PersonNum,Calls,AccTime): 100,1519,54.191s
        """
        graph = seq2graph(self.coordinates, directed)

        if edge_weighted_by_distance:
            for edge in graph.edges_iter():
                graph.edge[edge[0]][edge[1]]['distance'] = \
                    road_network.shortest_path_distance(edge[0], edge[1])

        if node_weighted_by_dwelling:
            for node in graph.nodes_iter():
                graph.node[node]['dwelling'] = self.accdwelling.get(node)

        return graph
