#!/usr/bin/env python
# -*- encoding: utf-8 -*-
import sys, os

import numpy as np

from xoxo.bsmap import BaseStationMap
from xoxo.permov import movement_reader
from xoxo.utils import dumps_mobgraph

__author__ = 'Xiaming Chen'
__email__ = 'chen@xiaming.me'


def validate_selfsim():
    ssfile = 'data/mesos0825_s0dot2/mesos0825_s0dot2_ssmode'
    movdata = 'data/hcl_mesos0825_sample0.2'
    bsmap = 'data/hcl_mesos0825_bm'
    ofname = 'data/mesos0825_s0dot2/mesos0825_s0dot2_ssmode_mg'

    users = {}
    i = 0
    for line in open(ssfile, 'rb'):
        if i == 0:
            i = 1
            continue

        parts = line.strip('\r\n').split(',')
        uid = int(parts[0])
        group = int(parts[1])
        clust = int(parts[2])
        dist = float(parts[3])
        selfdist = float(parts[4])
        mode = str(parts[5])

        users[uid] = (group, clust, dist, selfdist, mode)

    print len(users)

    ofile = open(ofname, 'wb')
    for person in movement_reader(open(movdata), BaseStationMap(bsmap)):
        if person.id not in users or person.distinct_loc_num() < 2:
            continue

        user = users[person.id]
        ofile.write('%d\t%d\t%d\t%.3f\t%.3f\t%s\t%s\n' % (
            person.id, user[0], user[1], user[2], user[3], user[4],
            dumps_mobgraph(person.convert2graph())))

    ofile.close()


if __name__ == '__main__':
    validate_selfsim()
