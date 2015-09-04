#!/usr/bin/env python
import networkx as nx
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import FancyArrowPatch, Circle

def draw_network(G,pos,ax,sg=None):

    for n in G:
        c=Circle(pos[n],radius=0.02,alpha=0.5)
        ax.add_patch(c)
        G.node[n]['patch']=c
        x,y=pos[n]
    seen={}
    for (u,v,d) in G.edges(data=True):
        n1=G.node[u]['patch']
        n2=G.node[v]['patch']
        rad=0.1
        if (u,v) in seen:
            rad=seen.get((u,v))
            rad=(rad+np.sign(rad)*0.1)*-1
        alpha=0.5
        color='k'

        e = FancyArrowPatch(n1.center,n2.center,patchA=n1,patchB=n2,
                            arrowstyle='-|>',
                            connectionstyle='arc3,rad=%s'%rad,
                            mutation_scale=10.0,
                            lw=2,
                            alpha=alpha,
                            color=color)
        seen[(u,v)]=rad
        ax.add_patch(e)
    return e


G=nx.MultiDiGraph([(1,2),(1,2),(2,3),(3,4),(2,4),
                (1,2),(1,2),(1,2),(2,3),(3,4),(2,4)]
                )

pos=nx.spring_layout(G)
ax=plt.gca()
draw_network(G,pos,ax)
ax.autoscale()
plt.axis('equal')
plt.axis('off')
plt.savefig("graph.pdf")
plt.show()