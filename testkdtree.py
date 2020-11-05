import KDTree

from timeit import default_timer as timer
#eisagwgi tou dataset
#tous xronous mporeite na tous deite metaferontas tis 3 entoles tou timer
import csv
results = []
with open("5000dataset.csv") as csvfile:
    reader = csv.reader(csvfile) # change contents to floats
    for row in reader: # each row is a list
        results.append(row)

#dimiourgia tou dentrou
tree = KDTree.create(dimensions=2)

#loop insert ta simeia tou csv
for x in range(5010):
        tree.insert([int(results[x][0]),int(results[x][1])])
        
if tree.is_balanced == False:
            tree = tree.rebalance()

#elegxos an to dentro einai balanced
if tree.is_balanced == False:
    tree = tree.rebalance()


print(tree)

#diagrafi enos simeiou
start = timer()

tree.delete([int(results[3739][0]),int(results[3739][1])])



#eisagwgi enos simeiou

tree.insert([int(results[5012][0]),int(results[5012][1])])


end = timer()
print(end - start) 

print(tree)


#arxi timer gia metrisi xronou

#anazitisi an ena simeio yparxei sto dentro
print(tree.search_nn([322365,530808]))
#anatisi knn , to 3346 einai to k , o arithmos geitonwn pou theloume na broume
print(tree.search_knn([844535, 424642] ,3346))
#telos timer 

tree.delete([int(results[2][0]),int(results[2][1])])

