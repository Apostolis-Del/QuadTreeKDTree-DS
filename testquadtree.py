from QuadTree import Node
from timeit import default_timer as timer

import QuadTree
import csv
import numpy as np

#dimiourgia quadtree
qt = Node(0, 0, 100000000000, 100000000000)

nodes = []

#anoigma csv
results = []
with open("5000dataset.csv") as csvfile:
    reader = csv.reader(csvfile) 
    for row in reader: 
        results.append(row)

for x in range(5015):
        nodes.append(Node(int(results[x][0]),int(results[x][1]),int(results[x][0]),int(results[x][1])))

#eisagwgi stoixeiwn
for x in range(5010):
        qt.insert(nodes[x])
#arxi timer
start = timer()
#reinsert stoixeiou 
qt.reinsert(nodes[6])
#telos timer 
end = timer()
print(end - start)
#delete stoixeiou
qt.delete(nodes[15])
#insert stoixeio
qt.insert(nodes[5013])