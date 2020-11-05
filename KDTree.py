# -*- coding: utf-8 -*-




from __future__ import print_function

import heapq
import itertools
import operator
import math
from collections import deque
from functools import wraps


class Node(object):
    

    def __init__(self, data=None, left=None, right=None):
        self.data = data
        self.left = left
        self.right = right


    @property
    def is_leaf(self):
       
        return (not self.data) or \
               (all(not bool(c) for c, p in self.children))


    def preorder(self):

        if not self:
            return

        yield self

        if self.left:
            for x in self.left.preorder():
                yield x

        if self.right:
            for x in self.right.preorder():
                yield x


    def inorder(self):

        if not self:
            return

        if self.left:
            for x in self.left.inorder():
                yield x

        yield self

        if self.right:
            for x in self.right.inorder():
                yield x


    def postorder(self):

        if not self:
            return

        if self.left:
            for x in self.left.postorder():
                yield x

        if self.right:
            for x in self.right.postorder():
                yield x

        yield self


    @property
    def children(self):
        

        if self.left and self.left.data is not None:
            yield self.left, 0
        if self.right and self.right.data is not None:
            yield self.right, 1


    def set_child(self, index, child):
       
        if index == 0:
            self.left = child
        else:
            self.right = child


    def height(self):
        

        min_height = int(bool(self))
        return max([min_height] + [c.height()+1 for c, p in self.children])


    def get_child_pos(self, child):

        for c, pos in self.children:
            if child == c:
                return pos


    def __repr__(self):
        return '<%(cls)s - %(data)s>' % \
            dict(cls=self.__class__.__name__, data=repr(self.data))


    def __nonzero__(self):
        return self.data is not None

    __bool__ = __nonzero__

    def __eq__(self, other):
        if isinstance(other, tuple):
            return self.data == other
        else:
            return self.data == other.data

    def __hash__(self):
        return id(self)


def require_axis(f):

    @wraps(f)
    def _wrapper(self, *args, **kwargs):
        if None in (self.axis, self.sel_axis):
            raise ValueError('%(func_name) requires the node %(node)s '
                    'to have an axis and a sel_axis function' %
                    dict(func_name=f.__name__, node=repr(self)))

        return f(self, *args, **kwargs)

    return _wrapper



class KDNode(Node):


    def __init__(self, data=None, left=None, right=None, axis=None,
            sel_axis=None, dimensions=None):
        
        super(KDNode, self).__init__(data, left, right)
        self.axis = axis
        self.sel_axis = sel_axis
        self.dimensions = dimensions


    @require_axis
    def insert(self, point):
       

        current = self
        while True:
            check_dimensionality([point], dimensions=current.dimensions)

            # Adding has hit an empty leaf-node, add here
            if current.data is None:
                current.data = point
                return current

            # split on self.axis, recurse either left or right
            if point[current.axis] < current.data[current.axis]:
                if current.left is None:
                    current.left = current.create_subnode(point)
                    return current.left
                else:
                    current = current.left
            else:
                if current.right is None:
                    current.right = current.create_subnode(point)
                    return current.right
                else:
                    current = current.right


    @require_axis
    def create_subnode(self, data):

        return self.__class__(data,
                axis=self.sel_axis(self.axis),
                sel_axis=self.sel_axis,
                dimensions=self.dimensions)


    @require_axis
    def find_replacement(self):
       
        if self.right:
            child, parent = self.right.extreme_child(min, self.axis)
        else:
            child, parent = self.left.extreme_child(max, self.axis)

        return (child, parent if parent is not None else self)


    def should_delete(self, point, node):
        if not self.data == point:
            return False
            

        return (node is None) or (node is self)

   
    @require_axis
    def delete(self, point, node=None):
        
        if not self:
            return

        if self.should_delete(point, node):
            return self._delete(point)

        if self.left and self.left.should_delete(point, node):
            self.left = self.left._delete(point)

        elif self.right and self.right.should_delete(point, node):
            self.right = self.right._delete(point)

        if point[self.axis] <= self.data[self.axis]:
            if self.left:
                self.left = self.left.delete(point, node)

        if point[self.axis] >= self.data[self.axis]:
            if self.right:
                self.right = self.right.delete(point, node)

        return self


    @require_axis
    def _delete(self, point):
        
        if self.is_leaf:
            self.data = None
            return self

       
        root, max_p = self.find_replacement()

      
        tmp_l, tmp_r = self.left, self.right
        self.left, self.right = root.left, root.right
        root.left, root.right = tmp_l if tmp_l is not root else self, tmp_r if tmp_r is not root else self
        self.axis, root.axis = root.axis, self.axis

        if max_p is not self:
            pos = max_p.get_child_pos(root)
            max_p.set_child(pos, self)
            max_p.delete(point, self)

        else:
            root.delete(point, self)

        return root


    @property
    def is_balanced(self):
       

        left_height = self.left.height() if self.left else 0
        right_height = self.right.height() if self.right else 0

        if abs(left_height - right_height) > 1:
            return False

        return all(c.is_balanced for c, _ in self.children)


    def rebalance(self):
        

        return create([x.data for x in self.inorder()])


    def axis_dist(self, point, axis):
       
        return math.pow(self.data[axis] - point[axis], 2)


    def dist(self, point):
      
        r = range(self.dimensions)
        return sum([self.axis_dist(point, i) for i in r])


    def search_knn(self, point, k, dist=None):
     

        if k < 1:
            raise ValueError("k must be greater than 0.")

        if dist is None:
            get_dist = lambda n: n.dist(point)
        else:
            get_dist = lambda n: dist(n.data, point)

        results = []

        self._search_node(point, k, results, get_dist, itertools.count())

      
        return [(node, -d) for d, _, node in sorted(results, reverse=True)]
    

    def _search_node(self, point, k, results, get_dist, counter):
        if not self:
            return

        nodeDist = get_dist(self)

       
        item = (-nodeDist, next(counter), self)
        if len(results) >= k:
            if -nodeDist > results[0][0]:
                heapq.heapreplace(results, item)
        else:
            heapq.heappush(results, item)
        split_plane = self.data[self.axis]
        plane_dist = point[self.axis] - split_plane
        plane_dist2 = plane_dist * plane_dist

        if point[self.axis] < split_plane:
            if self.left is not None:
                self.left._search_node(point, k, results, get_dist, counter)
        else:
            if self.right is not None:
                self.right._search_node(point, k, results, get_dist, counter)

        if -plane_dist2 > results[0][0] or len(results) < k:
            if point[self.axis] < self.data[self.axis]:
                if self.right is not None:
                    self.right._search_node(point, k, results, get_dist,
                                            counter)
            else:
                if self.left is not None:
                    self.left._search_node(point, k, results, get_dist,
                                           counter)


    @require_axis
    def search_nn(self, point, dist=None):
        
        return next(iter(self.search_knn(point, 1, dist)), None)


    def _search_nn_dist(self, point, dist, results, get_dist):
        if not self:
            return

        nodeDist = get_dist(self)

        if nodeDist < dist:
            results.append(self.data)

        split_plane = self.data[self.axis]

        if point[self.axis] <= split_plane + dist:
            if self.left is not None:
                self.left._search_nn_dist(point, dist, results, get_dist)
        if point[self.axis] >= split_plane - dist:
            if self.right is not None:
                self.right._search_nn_dist(point, dist, results, get_dist)


    @require_axis
    def search_nn_dist(self, point, distance, best=None):
      

        results = []
        get_dist = lambda n: n.dist(point)

        self._search_nn_dist(point, distance, results, get_dist)
        return results


    @require_axis
    def is_valid(self):
        
        if not self:
            return True

        if self.left and self.data[self.axis] < self.left.data[self.axis]:
            return False

        if self.right and self.data[self.axis] > self.right.data[self.axis]:
            return False

        return all(c.is_valid() for c, _ in self.children) or self.is_leaf


    def extreme_child(self, sel_func, axis):
       
        max_key = lambda child_parent: child_parent[0].data[axis]


        me = [(self, None)] if self else []

        child_max = [c.extreme_child(sel_func, axis) for c, _ in self.children]
        child_max = [(c, p if p is not None else self) for c, p in child_max]

        candidates =  me + child_max

        if not candidates:
            return None, None

        return sel_func(candidates, key=max_key)



def create(point_list=None, dimensions=None, axis=0, sel_axis=None):
    
    if not point_list and not dimensions:
        raise ValueError('either point_list or dimensions must be provided')

    elif point_list:
        dimensions = check_dimensionality(point_list, dimensions)

    # by default cycle through the axis
    sel_axis = sel_axis or (lambda prev_axis: (prev_axis+1) % dimensions)

    if not point_list:
        return KDNode(sel_axis=sel_axis, axis=axis, dimensions=dimensions)

    # Sort point list and choose median as pivot element
    point_list = list(point_list)
    point_list.sort(key=lambda point: point[axis])
    median = len(point_list) // 2

    loc   = point_list[median]
    left  = create(point_list[:median], dimensions, sel_axis(axis))
    right = create(point_list[median + 1:], dimensions, sel_axis(axis))
    return KDNode(loc, left, right, axis=axis, sel_axis=sel_axis, dimensions=dimensions)


def check_dimensionality(point_list, dimensions=None):
    dimensions = dimensions or len(point_list[0])
    for p in point_list:
        if len(p) != dimensions:
            raise ValueError('All Points in the point_list must have the same dimensionality')
    return dimensions



def level_order(tree, include_all=False):
   
    q = deque()
    q.append(tree)
    while q:
        node = q.popleft()
        yield node

        if include_all or node.left:
            q.append(node.left or node.__class__())

        if include_all or node.right:
            q.append(node.right or node.__class__())
