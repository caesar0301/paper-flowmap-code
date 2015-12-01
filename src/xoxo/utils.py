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
from datetime import datetime
import os
import zipfile
import fnmatch
import random
import string

import shapefile
import numpy as np
import networkx as nx
import matplotlib.pyplot as plt


__all__ = ['drange', 'in_area', 'seq2graph', 'greate_circle_distance', 'shape2points',
           'randstr', 'zipdir', 'zippylib']

try:
    from matplotlib.patches import FancyArrowPatch, Circle
    __all__.append('draw_network')
except:
    print("Warnning: install `matplotlib` to use draw_network().")


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


def in_area(p, lb = [120.03013, 30.13614], rt = [120.28597, 30.35318]):
    """Check if a point (lon, lat) is in an area denoted by
    the left-below and right-top points.
    """
    if p[0] >= lb[0] and p[0] <= rt[0] and p[1] >= lb[1] and p[1] <= rt[1]:
        return True
    return False


def seq2graph(seq, directed=True):
    """Create a directed graph from an odered
    sequence of items.

    An alternative to nx.Graph.add_path().
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
    # ax=plt.gca()
    # pos=nx.spring_layout(motif)
    # draw_network(motif, pos, ax)


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

    # ax.autoscale()
    # plt.axis('equal')
    # plt.axis('off')

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


def radius_of_gyration(coordinates):
    """ Calculate the radius of gyration given a list of [(lons, lats)]
    """
    clon = np.average([coord[0] for coord in coordinates])
    clat = np.average([coord[1] for coord in coordinates])

    return np.average([greate_circle_distance(clon, clat, coord[0], coord[1]) for coord in coordinates])


def shape2points(shpfile):
    """Extract point coordinats from a ERIS point shapefile.
    """
    sf = shapefile.Reader(shpfile)
    return [shape.points[0] for shape in sf.shapes()]


def randstr(len):
    return ''.join(random.choice(string.lowercase) for i in range(len))


def zipdir(path, zipf=None, fnpat='*'):
    """
    Parameters
    ----------
    path:
        folder containing plain files to zip
    zipf:
        path to store zipped file
    fnpat:
        Unix shell-style wildcards supported by
        `fnmatch.py <https://docs.python.org/2/library/fnmatch.html>`_
    """
    if zipf is None:
        zipf = '/tmp/xoxo-' + randstr(10) + '.zip'
    elif zipf[-4:] != '.zip':
        zipf = zipf + ".zip"
    ziph = zipfile.ZipFile(zipf, 'w')
    try:
        for root, dirs, files in os.walk(path):
            for file in files:
                if fnmatch.fnmatch(file, fnpat):
                    ziph.write(os.path.join(root, file))
        return zipf
    finally:
        ziph.close()


def zippylib(libpath, zipf=None):
    """ A particular zip utility for python module.
    """
    if zipf is None:
        zipf = '/tmp/xoxo-' + randstr(10) + '.zip'
    elif zipf[-4:] != '.zip':
        zipf = zipf + ".zip"
    ziph = zipfile.PyZipFile(zipf, 'w')
    try:
        ziph.debug = 3
        ziph.writepy(libpath)
        return zipf
    finally:
        ziph.close()


def normalized(a, axis=None, order=2):
    l2 = np.atleast_1d(np.linalg.norm(a, order, axis))
    l2[l2==0] = 1
    return a / l2


def dumps_mobgraph(G, node_attribute='weight', edge_attribute='weight', norm=True):
    """ Save a mobility graph to string
    """
    assert isinstance(G, nx.DiGraph)
    nw = []
    ew = []
    node_index = {}
    for node in G.nodes():
        if node not in node_index:
            node_index[node] = len(node_index)
        nw.append((node, G.node[node][node_attribute]))
    for es, et in G.edges():
        ew.append((node_index[es], node_index[et], G[es][et][edge_attribute]))

    if norm:
        nwsum = np.sum([i[1] for i in nw])
        nw = [(i[0], i[1]/nwsum) for i in nw]
        ewsum = np.sum([i[2] for i in ew])
        ew = [(i[0], i[1], i[2]/ewsum) for i in ew]

    nodestr = ';'.join(['%s,%.3f' % (str(n[0]), float(n[1])) for n in nw])
    edgestr = ';'.join(['%d,%d,%.3f' % (e[0], e[1], float(e[2])) for e in ew])
    return '%s|%s' % (nodestr, edgestr)


def loads_mobgraph(S, node_attribute='weight', edge_attribute='weight'):
    """ Load a mobility graph from a string representation
    """
    nodestr, edgestr = S.split('|')
    nodes = nodestr.split(';')
    edges = edgestr.split(';')

    node_rindex = {}
    for nid in range(0, len(nodes)):
        n, w = nodes[nid].rsplit(',', 1)
        node_rindex[nid] = (n, float(w))

    G = nx.DiGraph()
    for e in edges:
        es, et, ew = e.split(',')
        es, nsw = node_rindex[int(es)]
        et, ntw = node_rindex[int(et)]
        G.add_edge(es, et)
        G.edge[es][et][edge_attribute] = float(ew)
        G.node[es][node_attribute] = nsw
        G.node[et][node_attribute] = ntw

    return G
