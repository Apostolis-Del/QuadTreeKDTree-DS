
import heapq
import itertools
import operator
import math
from collections import deque
from functools import wraps
import numpy as np


def fits(bounds_inside, bounds_around):
    x1_min, y1_min, x1_max, y1_max = bounds_inside
    x2_min, y2_min, x2_max, y2_max = bounds_around
    return (x1_min >= x2_min and x1_max <= x2_max
            and y1_min >= y2_min and y1_max <= y2_max)


def overlaps(bounds_A, bounds_B):
    x1_min, y1_min, x1_max, y1_max = bounds_A
    x2_min, y2_min, x2_max, y2_max = bounds_B
    x_overlaps = (x1_min <= x2_min <= x1_max) or (x2_min <= x1_min <= x2_max)
    y_overlaps = (y1_min <= y2_min <= y1_max) or (y2_min <= y1_min <= y2_max)
    return x_overlaps and y_overlaps


def fix_bounds(bounds):
    x1, y1, x2, y2 = bounds
    if x1 > x2:
        x1, x2 = x2, x1
    if y1 > y2:
        y1, y2 = y2, y1
    return (x1, y1, x2, y2)


class Node(object):
    def __init__(self, x_min, y_min, x_max, y_max, max_depth=4, parent=None):
        if x_min > x_max:
            raise ValueError("x_min cannot be greater than x_max")
        if y_min > y_max:
            raise ValueError("y_min cannot be greater than y_max")
        if max_depth < 0:
            raise ValueError("max_depth cannot be less than 0")
        self.x_min = x_min
        self.y_min = y_min
        self.x_max = x_max
        self.y_max = y_max
        self.max_depth = max_depth
        self.direct_children = []
        self.quadrants = []
        self.parent = parent
        self.bounds = (x_min, y_min, x_max, y_max)

    def subdivide(self):
        x_min, y_min = self.x_min, self.y_min
        x_max, y_max = self.x_max, self.y_max
        x_center = (x_min + x_max) / 2.0
        y_center = (y_min + y_max) / 2.0
        depth = self.max_depth - 1
        self.quadrants = [
            Node(x_min, y_min, x_center, y_center, depth, self),
            Node(x_center, y_min, x_max, y_center, depth, self),
            Node(x_min, y_center, x_center, y_max, depth, self),
            Node(x_center, y_center, x_max, y_max, depth, self),
        ]

    def clear(self):
        self.direct_children = []
        [q.clear() for q in self.quadrants]
        self.quadrants = []

    def insert(self, child):
        if fits(child.bounds, self.bounds):
            self._insert(child)
        else:
            self.direct_children.append(child)
            child.qt_data = (self, len(self.direct_children) - 1)
       

    def _insert(self, child):
        child.bounds = fix_bounds(child.bounds)

        if not self.quadrants and self.max_depth > 0:
            self.subdivide()

        for q in self.quadrants:
            if fits(child.bounds, q.bounds):
                q._insert(child)
                return
        self.direct_children.append(child)
        child.qt_data = (self, len(self.direct_children) - 1)

    def reinsert(self, child):
        parent, index = child.qt_data
        root = parent
        while root.parent:  # find root node
            root = root.parent
        parent._delete(child)
        root._reinsert(child)

    def _reinsert(self, child):
        if fits(child.bounds, self.bounds) or self.parent is None:
            self._insert(child)
        else:
            self.parent._reinsert(child)

    def delete(self, child):
        parent = child.qt_data[0]
        parent._delete(child)

    def _delete(self, child):
       
        num_children = len(self.direct_children)
        if num_children > 1:
            last = self.direct_children[num_children - 1]
            last.qt_data = child.qt_data
            self.direct_children[child.qt_data[1]] = last
            self.direct_children.pop()
        else:
            self.direct_children.pop()
            self._try_cleanup()

    def _try_cleanup(self):
   
        if not self.get_children():
            self.clear()
            if self.parent:
                self.parent._try_cleanup()

    def get_children(self):
        subchildren = [ch for q in self.quadrants for ch in q.get_children()]
        return self.direct_children + subchildren

    def get_enclosed_children(self, within_bounds):
        within_bounds = fix_bounds(within_bounds)

        if not overlaps(within_bounds, self.bounds):
            return []

        if fits(self.bounds, within_bounds):
            return self.get_children()

        enclosed_subchildren = [ch for q in self.quadrants for ch
                                in q.get_enclosed_children(within_bounds)]
        enclosed_children = [ch for ch in self.direct_children
                             if fits(ch.bounds, within_bounds)]

        return enclosed_children + enclosed_subchildren

    def get_overlapped_children(self, bounds):
        bounds = fix_bounds(bounds)

        if not overlaps(bounds, self.bounds):
            return []

        if fits(self.bounds, bounds):
            return self.get_children()

        overlapped_subchildren = [ch for q in self.quadrants
                                  for ch in q.get_overlapped_children(bounds)]
        overlapped_children = [ch for ch in self.direct_children
                               if overlaps(ch.bounds, bounds)]

        return overlapped_children + overlapped_subchildren

    def get_children_under_point(self, x, y):  
        return self.get_overlapped_children((x, y, x, y))  

    def _get_depth(self):
        if not self.quadrants:
            return 0
        return 1 + max(q._get_depth() for q in self.quadrants)

    def _get_number_of_nodes(self):
        if not self.quadrants:
            return 1
        return 1 + sum(q._get_number_of_nodes() for q in self.quadrants)

    def _get_grid_bounds(self):
        if not self.quadrants:
            return [self.bounds]
        return [b for q in self.quadrants for b in q._get_grid_bounds()]

    def __repr__(self):
        params = [str(p) for p in list(self.bounds) + [self.max_depth,
                                                       self.parent]]
        return "{0}({1})".format(self.__class__.__name__, ', '.join(params))
    
