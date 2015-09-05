#!/usr/bin/env python
# Read the movement history and mobile network topology
# By mxc
import sys
from datetime import datetime, date

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
            self.load_db(path)

    def load_db(self, path):
        print("loading cell map database ...")
        for line in open(path, 'rb'):
            parts = line.strip('\r\n ').split(',')
            id = int(parts[0])
            lon = float(parts[2])
            lat = float(parts[3])
            self._mapDB[id] = (lon, lat)

    def validate_db(self):
        if len(self._mapDB) == 0:
            print("ERROR: the map DB is not initialized, exiting")
            sys.exit(1)

    def get_with_id(self, id):
        self.validate_db()
        return self._mapDB[id]

    def get_with_ids(self, ids):
        self.validate_db()
        return [ self._mapDB[i] for i in ids ]


class PersonMoveDay(object):

    def __init__(self, user_id, dtstart, timestamps, locations):
        assert isinstance(dtstart, datetime)
        assert isinstance(timestamps, list)
        assert isinstance(locations, list)

        self.user_id = user_id
        self.dtstart = dtstart

        ## remove duplicate stays
        nodup = []
        last = None
        for i in range(0, len(locations)):
            if locations[i] != last:
                nodup.append(i)
            last = locations[i]
        self.timestamps = [timestamps[i] for i in nodup]
        self.locations = [locations[i] for i in nodup]

        ## mine circle movement path
        self.circles = self.mine_circles(self.locations)

        ## dwelling time
        self.dwelling = []

    def __str__(self):
        return 'User %d: %s %d %s' % (
            self.user_id,
            self.dtstart.strftime('%Y%m%d'),
            len(self.circles),
            self.locations
            )

    def mine_circles(self, locs):
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
                    deeper = self.mine_circles(locs[i+1:j])
                    deeper = [(t[0]+i+1, t[1]+i+1) for t in deeper]
                    circles.extend(deeper)
                    break
            i = j if found else (i + 1)
        return circles


def movement_reader(fname):
    """ An iterator to read personal daily data.
    """
    buf_ts = []
    buf_lc = []
    last_uid = None
    last_day_start = None

    def check_time_alignment():
        if buf_ts[-1] != buf_ts[0] + 86400:
            buf_ts.append(buf_ts[0] + 86400)
            buf_lc.append(buf_lc[0])

    for line in open(fname, 'rb'):
        line = line.strip('\r\n ')

        if line.startswith('#'): continue

        uid, ts, loc = line.split(',')[0:3]
        uid = int(uid); ts = int(float(ts)); loc = int(loc)
        dt = datetime.fromtimestamp(ts)
        day_start, day_end = drange(ts)

        if not is_valid_location(loc):
            continue

        if last_uid is None or uid == last_uid and day_start == last_day_start:
            buf_ts.append(ts)
            buf_lc.append(loc)
        else: # manipulate the buffer
            check_time_alignment()
            yield PersonMoveDay(last_uid, last_day_start, buf_ts, buf_lc)

            buf_ts = [ts]
            buf_lc = [loc]

        last_uid = uid
        last_day_start = day_start

    check_time_alignment()
    yield PersonMoveDay(last_uid, last_day_start, buf_ts, buf_lc)


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


def is_valid_location(location_id):
    """ Check if given location point is valid
    """
    HZ_LB = [120.03013, 30.13614]
    HZ_RT = [120.28597, 30.35318]
    cmap = CellMapDB()  # get network map
    coord = cmap.get_with_id(location_id)
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
