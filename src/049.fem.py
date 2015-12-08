#!/usr/bin/env python
# -*- encoding: utf-8 -*-
import sys, os

import numpy as np
import networkx as nx
from scipy.stats import rv_continuous, lognorm

from xoxo.permov import movement_reader
from xoxo.bsmap import BaseStationMap
from xoxo.utils import greate_circle_distance, radius_of_gyration


__author__ = 'Xiaming Chen'
__email__ = 'chen@xiaming.me'


def load_oppmap(bsmap):
    """ Draw opportunity map from Flowmap
    """
    ifname = 'data/hcl_mesos0825_flowmap'

    last_interval = None
    graph = nx.Graph()
    nw = {}

    for line in open(ifname, 'rb'):
        interval, src, dst, total, unique = line.strip('\r\n').split(',')
        interval = int(interval)
        src = bsmap.get_coordinates(int(src))
        dst = bsmap.get_coordinates(int(dst))
        total = int(total)
        unique = int(unique)

        # if last_interval and interval != last_interval:
        #     break

        if dst not in nw:
            nw[dst] = unique
        else:
            nw[dst] += unique

        if unique > 20:
            graph.add_edge(src, dst)

        last_interval = interval

    for nid in graph.nodes():
        if nid in nw:
            graph.node[nid]['weight'] = nw[nid]
        else:
            graph.node[nid]['weight'] = 0

    print len(graph.nodes())

    return graph


def load_dtmodels():
    """ Read dwelling time models
    """
    ifname = 'data/hcl_mesos7d_dtloc_log_model_clean'

    models = []
    i = 0
    for line in open(ifname, 'rb'):
        if i == 0:
            i = 1
            continue

        uid, mu1 ,mu2, sigma1, sigma2, lamb = line.strip('\r\n').split(',')
        models.append((float(mu1), float(mu2), float(sigma1), float(sigma2), float(lamb)))

    return models


class DtGenerator(rv_continuous):
    """ Generate two-mode lognormal dist for dwelling time
    """
    def _pdf(self, x, mu1, mu2, sigma1, sigma2, lamb):
        return lamb * lognorm.pdf(x, s=sigma1, scale=np.exp(mu1)) +\
               (1 - lamb) * lognorm.pdf(x, s=sigma2, scale=np.exp(mu2))


def random_dt(mu1, mu2, sigma1, sigma2, lamb):
    dg = DtGenerator(name='dtdist', a=0.1, b=8)
    dt = dg.rvs(mu1, mu2, sigma1, sigma2, lamb)
    return dt


class RgGenerator(rv_continuous):
    """ Generate random R_g according to empirical distribution. Ref. mesos paper
    """
    def _pdf(self, x):
        return np.exp(-2.36 + 0.601 * x - 0.141 * np.power(x, 2)) * np.power(x, 0.22)

gen_rg = RgGenerator(name='rgdist', a = 0.5, b = 10)


def person_map(curlocs, rg, global_opmap):
    """ Generate individual's map
    """
    assert isinstance(curlocs, list)

    iops = []
    for node in global_opmap.nodes():
        s = [node]
        s.extend(curlocs)
        if radius_of_gyration(s) <= rg:
            iops.append(node)

    return iops


def gen_random_home(opmap):
    """ Select random location from opportunity map
    """
    locs = [i[0] for i in opmap.nodes(data=True)]
    return locs[np.random.random_integers(len(locs))]


def model_random():
    ofname = 'data/mesos_model_rwm_stat'
    ofile = open(ofname, 'wb')

    bsmap = BaseStationMap('data/hcl_mesos0825_bm')
    opmap = load_oppmap(bsmap)
    dtmodel = load_dtmodels()
    nmodel = len(dtmodel)

    TIMEBOUND = 18

    for j in range(1, 1000):
        # User profile
        uid = j
        dtm = dtmodel[np.random.random_integers(nmodel)]
        rhome = gen_random_home(opmap)

        rg = gen_rg.rvs()
        print '%d: %.3f' % (uid, rg)

        traj = [rhome]
        traj_dts = [6]
        acctime = 0
        isvalid = True
        while acctime < TIMEBOUND:
            print acctime

            # determine dwelling time
            dt = random_dt(dtm[0], dtm[1], dtm[2], dtm[3], dtm[4])
            if acctime + dt > TIMEBOUND:
                dt = TIMEBOUND - acctime

            traj_dts.append(dt)
            acctime += dt

            # determine location
            try:
                iops = person_map(traj, rg, opmap)
                nextloc = iops[np.random.random_integers(len(iops))]
                traj.append(nextloc)
            except:
                isvalid = False

        if not isvalid:
            print isvalid
            continue

        traj.append(rhome)
        traj_dts.append(0)

        # stat
        totloc = len(set(traj))
        dtloc = {}
        for l in range(len(traj)):
            if traj[l] not in dtloc:
                dtloc[traj[l]] = 0
            dtloc[traj[l]] += traj_dts[l]
        trvdist = [greate_circle_distance(traj[i][0], traj[i][1], traj[i+1][0], traj[i+1][1]) for i in range(len(traj)-1)]
        totdist = np.sum(trvdist)

        print trvdist

        ofile.write('%d\t%.3f\t%d\t%.3f\t%s\n' % (
            uid, rg, totloc, totdist,
            ','.join(['%.3f' % i for i in trvdist]),
            ))

    ofile.close()


def model_maxoppo():
    ofname = 'data/mesos_model_mom_stat'
    ofile = open(ofname, 'wb')

    bsmap = BaseStationMap('data/hcl_mesos0825_bm')
    opmap = load_oppmap(bsmap)
    dtmodel = load_dtmodels()
    nmodel = len(dtmodel)

    TIMEBOUND = 18

    for j in range(1, 1000):
        # User profile
        uid = j
        dtm = dtmodel[np.random.random_integers(nmodel)]
        rhome = gen_random_home(opmap)

        rg = gen_rg.rvs()
        print '%d: %.3f' % (uid, rg)

        traj = [rhome]
        traj_dts = [6]
        acctime = 0
        isvalid = True
        while acctime < TIMEBOUND:
            print acctime

            # determine dwelling time
            dt = random_dt(dtm[0], dtm[1], dtm[2], dtm[3], dtm[4])
            if acctime + dt > TIMEBOUND:
                dt = TIMEBOUND - acctime

            traj_dts.append(dt)
            acctime += dt

            # determine location
            try:
                iops = person_map(traj, rg, opmap)
                maxloc = rhome
                maxdist = 0
                for i in iops:
                    if i != traj[-1]:
                        dist = greate_circle_distance(i[0], i[1], traj[-1][0], traj[-1][1])
                        if dist > maxdist:
                            maxloc = i
                            maxdist = dist
                traj.append(maxloc)
            except:
                isvalid = False

        if not isvalid:
            print isvalid
            continue

        traj.append(rhome)
        traj_dts.append(0)

        # stat
        totloc = len(set(traj))
        dtloc = {}
        for l in range(len(traj)):
            if traj[l] not in dtloc:
                dtloc[traj[l]] = 0
            dtloc[traj[l]] += traj_dts[l]
        trvdist = [greate_circle_distance(traj[i][0], traj[i][1], traj[i+1][0], traj[i+1][1]) for i in range(len(traj)-1)]
        totdist = np.sum(trvdist)

        print trvdist

        ofile.write('%d\t%.3f\t%d\t%.3f\t%s\n' % (
            uid, rg, totloc, totdist,
            ','.join(['%.3f' % i for i in trvdist]),
        ))

    ofile.close()


def empirical_data():
    ifname = 'data/hcl_mesos0822_sample0.2'
    bsmap = bsmap = BaseStationMap('data/hcl_mesos0822_bm')
    ofile = open('data/mesos_model_emp_stat2', 'wb')

    for person in movement_reader(open(ifname), bsmap):
        if len(person) < 2:
            continue

        uid = person.id
        rg = person.radius_of_gyration()
        totloc = len(set(person.locations))
        traj = person.coordinates
        trvdist = [greate_circle_distance(traj[i][0], traj[i][1], traj[i+1][0], traj[i+1][1]) for i in range(len(traj)-1)]
        totdist = np.sum(trvdist)

        ofile.write('%d\t%.3f\t%d\t%.3f\t%s\n' % (
            uid, rg, totloc, totdist,
            ','.join(['%.3f' % i for i in trvdist]),
        ))

    ofile.close()



if __name__ == '__main__':
    empirical_data()