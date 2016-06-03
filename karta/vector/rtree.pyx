""" Cython wrapper for rtree """

cdef enum Strategy:
    LINEAR, QUADRATIC

cdef enum NodeType:
    LEAF, NONLEAAF

cdef struct BoundingBox:
    float xmin
    float ymin
    float xmax
    float ymax

ctypedef BoundingBox Bbox

cdef struct RTreeNode:
    NodeType type
    Strategy strategy
    int count
    int maxchildren
    RTreeNode* parent
    char** children
    int* indices
    Bbox* bbox

ctypedef RTreeNode Node

cdef struct PointerPool:
    int size
    char **members
    int count

ctypedef PointerPool Pool

cdef extern from "rtree.h":
    Node* rt_new_node(NodeType, Strategy, int, Node*)
    Node* rt_insert(Node*, Bbox*, int)
    Bbox* rt_new_bbox()
    void rt_free(Node*)
    void print_bbox(Bbox*)
    Pool *rt_search_within(Node*, Bbox*, int)
    Pool *rt_search_overlapping(Node*, Bbox*, int)

    char *pool_pop(Pool*, int)
    void pool_destroy(Pool*)

cdef class RTree:
    cdef list geometries
    cdef Node* root

    def __init__(self, list geometries, maxchildren=50):
        cdef int i
        cdef object geom
        cdef Node* root

        root = rt_new_node(LEAF, LINEAR, maxchildren, NULL)
        for i, geom in enumerate(geometries):
            _bb = geom.bbox
            bb = rt_new_bbox()
            bb.xmin = _bb[0]
            bb.ymin = _bb[1]
            bb.xmax = _bb[2]
            bb.ymax = _bb[3]
            root = rt_insert(root, bb, i)

        self.geometries = geometries
        self.root = root
        return

    def __dealloc__(self):
        rt_free(self.root)

    @property
    def bbox(self):
        return (self.root.bbox.xmin, self.root.bbox.ymin,
                self.root.bbox.xmax, self.root.bbox.ymax)

    def search_within(self, bbox, int max_results=-1):
        """ Return a list of geometries that are within a bounding box. """
        cdef Pool* result
        cdef Bbox* bb = rt_new_bbox()
        bb.xmin = bbox[0]
        bb.ymin = bbox[1]
        bb.xmax = bbox[2]
        bb.ymax = bbox[3]
        result = rt_search_within(self.root, bb, max_results)
        cdef list out = []
        while result.count != 0:
            out.append(self.geometries[(<int*> pool_pop(result, result.count-1))[0]])
        pool_destroy(result)
        return out

    def search_overlapping(self, bbox, int max_results=-1):
        """ Return a list of geometries that are within a bounding box. """
        cdef Pool* result
        cdef Bbox* bb = rt_new_bbox()
        bb.xmin = bbox[0]
        bb.ymin = bbox[1]
        bb.xmax = bbox[2]
        bb.ymax = bbox[3]
        result = rt_search_overlapping(self.root, bb, max_results)
        cdef list out = []
        while result.count != 0:
            out.append(self.geometries[(<int*> pool_pop(result, result.count-1))[0]])
        pool_destroy(result)
        return out
