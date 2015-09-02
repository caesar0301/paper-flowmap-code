import networkx  as nx
import shapefile
import numpy as np
import json

def shape2graph(shpfile, distance=True):
    """Converts a ERIS shapefile into an undirected graph in NetworkX.
    """
    g = nx.read_shp(shpfile)
    mg = max(nx.connected_component_subgraphs(g.to_undirected()), key=len)
    if distance: # add distance progperty to edges
        for n0, n1 in mg.edges_iter():
            # get an array of point coordinates along the road
            path = get_path_segment(mg, n0, n1)
            distance = get_path_length(path)
            mg.edge[n0][n1]['distance'] = distance
    return mg

def shape2points(shpfile):
    """Extract point coordinats from a ERIS point shapefile.
    """
    sf = shapefile.Reader(shpfile)
    return [ shape.points[0] for shape in sf.shapes()]

def get_path_segment(G, n0, n1):
    """If n0 and n1 are connected nodes in the graph, this function
    return an array of point coordinates along the road linking
    these two nodes.
    """
    return np.array(json.loads(G[n0][n1]['Json'])['coordinates'])

def get_path_length(path):
    """Return the total geographical distance between two
    origions of a path.
    """
    return np.sum(geocalc(path[1:,0], path[1:,1], path[:-1,0], path[:-1,1]))

def geocalc(lon0, lat0, lon1, lat1):
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

def shortest_path(G, lonlat1, lonlat2, weight='distance'):
    """Find the shortest path for a pair of points. These two points are not
    required to be the vertex of graph.
    """
    # Get the closest nodes in given graph
    nodes = np.array(G.nodes())
    p1 = np.argmin(np.sum((nodes[:,:] - lonlat1)**2, axis=1))
    p2 = np.argmin(np.sum((nodes[:,:] - lonlat2)**2, axis=1))
    # Get segments of shortest path
    path = nx.shortest_path(G, tuple(nodes[p1]), tuple(nodes[p2]), weight)
    return path
    
def shortest_distance(G, lonlat1, lonlat2, weight='distance'):
    """Return the distance of two points with the shortest path algorithm.
    """
    sp = shortest_path(G, lonlat1, lonlat2, weight)
    distances = [G.edge[sp[i]][sp[i+1]][weight] for i in range(len(sp)-1)]
    return np.sum(distances)

def spmatrix(G, points, weight='distance'):
    """ Return the pair-wise shortest distance matrix
    given a list of points.
    """
    def sp(i, j):
        return shortest_distance(G, points[i], points[j], weight)

    dMat = []
    for i in range(0, len(points)):
        v = [ sp(i, j) if i > j else 0 for j in range(0, len(points))]
        dMat.append(v)
    return np.array(dMat)

if __name__ == '__main__':
    sg = shape2graph('../map/hz/roads_clean.shp')
    points = shape2points('../map/hz/mobilenetwork.shp')[1:100]
    print len(points)
    print spmatrix(sg, points)