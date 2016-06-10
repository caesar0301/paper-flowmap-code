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

class BaseStationMap(object):
    """ A singleton to store mobile network topology
    """

    def __init__(self, path):
        self._mapDB = {}
        for line in open(path, 'rb'):
            parts = line.strip('\r\n ').split(',')
            id = int(parts[0])
            lon = float(parts[2])
            lat = float(parts[3])
            self._mapDB[id] = (lon, lat)

    def validate_database(self):
        if len(self._mapDB) == 0:
            print("ERROR: the map DB is not initialized, exiting")
            return False
        return True

    def get_coordinates(self, locationid):
        return self._mapDB[locationid] if self.validate_database() else None

    def get_coordinates_from(self, locationids):

        return [self._mapDB[i] for i in locationids] if self.validate_database() else None

    def get_all_coordinates(self):
        return self._mapDB.values()
