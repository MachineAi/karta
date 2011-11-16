#! /usr/bin/env python
#
#   guppy.py
#
# Geographical measurement and simple analysis module for Python
# 2.X.X. Provide point, polyline, and polygon classes, with methods
# for simple measurements such as distance, area, and bearing.
#
# Written by Nat Wilson (njwilson23@gmail.com)
#
#   Need to fill in Multipoint.closest_to() methods
#

import math
import sys
from collections import deque
import traceback
try:
    import shapely.geometry as geometry
except ImportError:
    pass

class Point(object):
    """ This defines the point class, from which x,y[,z] points can be
    constructed.
    """

    def __init__(self, coords):
        self.x = float(coords[0])
        self.y = float(coords[1])
        try:
            self.z = float(coords[2])
            self.rank = 3
        except IndexError:
            self.z = None
            self.rank = 2
        self.xy = (self.x, self.y)
        self.xyz = (self.x, self.y, self.z)

    def __repr__(self):
        if self.rank == 2:
            return 'point(' + str(self.xy) + ')'
        elif self.rank == 3:
            return 'point(' + str(self.xyz) + ')'

    def coords(self, convert_to=False):
        """ Returns the x,y coordinates. Convert_to may be set to 'deg'
        or 'rad' for convenience.  """
        if angle == 'rad':
            return (self.x*3.14159/180., self.y*3.14159/180.)
        elif angle == 'deg':
            return (self.x/3.14159*180., self.y/3.14159*180.)
        else:
            return (self.x, self.y)

    def bearing(self, other, spherical=False):
        """ Returns the bearing from self to other in radians. Returns
        None if points have equal x and y. See point.azimuth() for
        z-axis directions. """
        dx = self.x - other.x
        dy = self.y - other.y

        if spherical is False:
            if dx == 0.0:
                if dy > 0.0:
                    return 0.0
                elif dy < 0.0:
                    return math.pi
                else:
                    return None

            elif dy >= 0.0:
                return math.atan(dy / dx)

            else:
                return math.atan(dy / dx) + math.pi

        elif spherical is True:
            sys.stderr.write('Not implemented')
        else:
            raise Exception("Value for 'spherical' kwarg not understood")
        return

    def azimuth(self, other, spherical=False):
        """ Returns the aximuth from self to other in radians. Returns None
        if points are coincident. """

        if self.z is None:
            raise Exception("point.azimuth() cannot be called from a rank 2 coordinate.")
            sys.exit(1)
        elif other.z is None:
            raise Exception("point.azimuth() cannot be called on a rank 2 coordinate.")
            sys.exit(1)

        distxy = math.sqrt((self.x-other.x)**2. + (self.y-other.y)**2.)
        dz = self.z - other.z

        if spherical is False:
            if distxy == 0.0:
                if dz > 0.0:
                    return 0.5 * math.pi
                elif dz < 0.0:
                    return -0.5 * math.pi
                elif dz == 0.0:
                    return None
            else:
                return math.atan(dz / distxy)

        elif spherical is True:
            raise Exception("Not implemented")
        else:
            raise Exception("Value for 'spherical' kwarg not understood")
        return

    def walk(self, distance, bearing, azimuth=0.0, spherical=False):
        """ Wraps walk() """
        return walk(self, distance, bearing, azimuth=0.0, spherical=False)

    def distance(self, other):
        """ Returns a cartesian distance. """
        flat_dist = math.sqrt((self.x-other.x)**2. + (self.y-other.y)**2.)
        if self.z is None or other.z is None:
            return flat_dist
        else:
            return math.sqrt(flat_dist**2. + (self.z-other.z)**2.)

    def shift(self, shift_vector):
        """ Shift point by the amount given by a vector. Operation occurs
        in-place """
        if len(shift_vector) != self.rank:
            raise Exception('Shift vector length must equal geometry rank.')

        self.x += shift_vector[0]
        self.y += shift_vector[1]
        if self.rank == 3:
            self.z += shift_vector[2]
        return

    def to_shapely(self):
        """ Returns a Shapely Point instance. """
        try:
            return geometry.Point(self.x, self.y, self.z)
        except NameError:
            raise Exception('Shapely module did not import\n')


class Multipoint(object):
    """ This is a base class for the polyline and polygon classes. """

    def __init__(self, vertices):
        self.rank = len(vertices[0])
        if self.rank > 3 or self.rank < 2:
            raise Exception('Input must be doubles or triples\n')
        elif False in [self.rank==len(i) for i in vertices]:
            raise Exception('Input must have consistent rank\n')
        else:
            self.vertices = [tuple(i) for i in vertices]

    def print_vertices(self):
        """ Prints an enumerated list of indices. """
        for i,vertex in enumerate(self.vertices):
            print i,'\t',vertex

    def length(self, spherical=False):
        """ Returns the length of the line. """
        points = [point(i) for i in self.vertices]
        distances = [a.distance(b) for a,b in zip(points[:-1], points[1:])]
        return sum(distances)

    def shift(self, shift_vector):
        """ Shift feature by the amount given by a vector. Operation
        occurs in-place """
        if len(shift_vector) != self.rank:
            raise Exception('Shift vector length must equal geometry rank.')

        if self.rank == 2:
            f = lambda pt: (pt[0]+shift_vector[0], pt[1]+shift_vector[1])
        elif self.rank == 3:
            f = lambda pt: (pt[0]+shift_vector[0], pt[1]+shift_vector[1],
                            pt[2]+shift_vector[2])
        self.vertices = map(f, self.vertices)
        return

    def nearest_to(self, pt):
        """ Returns the point on the Multipoint boundary that is
        nearest to pt (point class).

        Warning: If two points are equidistant, only one will be
        returned.
        """
        point_dist = []

        rvertices = deque(self.vertices)
        rvertices.rotate(1)
        segments = [(v1, v2) for v1, v2 in zip(self.vertices, rvertices)]

        point_dist = map(pt_nearest, [pt.xy for seg in segments],
            [seg[0] for seg in segments], [seg[1] for seg in segments])
        distances = [i[1] for i in point_dist]

        return point(point_dist[distances.index(min(distances))][0])


class Polyline(Multipoint):
    """ This defines the polyline class, from which geographic line
    objects can be constructed. Line objects consist of joined,
    georeferenced line segments.
    """

    def __init__(self, vertices):
        Multipoint.__init__(self, vertices)

    def __repr__(self):
        return 'polyline(' + reduce(lambda a,b: str(a) + ' ' + str(b),
                self.vertices) + ')'

    def add_vertex(self, vertex):
        """ Add a vertex to self.vertices. """
        if isinstance(vertex, point):
            if self.rank == 2:
                self.vertices.append((vertex.x, vertex.y))
            elif self.rank == 3:
                self.vertices.append((vertex.x, vertex.y, vertex.z))
        else:
            if self.rank == 2:
                self.vertices.append((vertex[0], vertex[1]))
            elif self.rank == 3:
                self.vertices.append((vertex[0], vertex[1], vertex[2]))

    def remove_vertex(self, index):
        """ Removes a vertex from the register by index. """
        self.vertices.pop(index)

    def displacement(self, spherical=False):
        """ Returns the distance between the first and last vertex. """
        return point(self.vertices[0]).distance(point(self.vertices[-1]))

    def to_polygon(self):
        """ Returns a polygon. """
        return polygon(self.vertices)

    def to_shapely(self):
        """ Returns a Shapely LineString instance. """
        try:
            if self.rank == 2:
                return geometry.LineString([(v[0], v[1]) for v in self.vertices])
            elif self.rank == 3:
                return geometry.LineString([(v[0], v[1], v[2]) for v in self.vertices])
        except NameError:
            raise Exception('Shapely module did not import\n')


class Polygon(Multipoint):
    """ This defines the polygon class, from which geographic
    polygons objects can be created. Polygon objects consist of
    point nodes enclosing an area.
    """
    def __init__(self, vertices):
        Multipoint.__init__(self, vertices)
        if vertices[0] != vertices[-1]:
            vertices.append(vertices[0])

    def __repr__(self):
        return 'polygon(' + reduce(lambda a,b: str(a) + ' ' + str(b),
                self.vertices) + ')'

    perimeter = Multipoint.length

    def area(self):
        """ Return the area of the polygon. Only 2D at the moment. """
        a = 0.0
        for i in range(len(self.vertices)-1):
            a += (self.vertices[i][0] + self.vertices[i+1][0]) \
                * (self.vertices[i][1] - self.vertices[i+1][1])
        return abs(0.5 * a)

    def contains(self, pt):
        """ Returns True if pt is inside or on the boundary of the
        polygon, and False otherwise.
        """
        def possible(pt, v1, v2):
            """ Quickly assess potential for an intersection with an x+
            pointing ray based on Easy Cases. """
            if ( ((pt.y > v1[1]) is not (pt.y > v2[1]))
            and ((pt.x < v1[0]) or (pt.x < v2[0])) ):
                return True
            else:
                return False

        # Find how many boundaries a ray pointing out from point crosses
        bool2int = lambda tf: (tf and 1 or 0)
        rvertices = deque(self.vertices)
        rvertices.rotate(1)
        segments = [(v1, v2) for v1, v2 in zip(self.vertices, rvertices)
                    if possible(pt, v1, v2)]

        n_intersect = sum([bool2int(
            isinstance(ray_intersection(pt.xy, seg[0], seg[1]), tuple))
            for seg in segments])

        if n_intersect % 2 == 1:    # If odd, then point is inside
            return True
        else:                   # If even, then point is outside
            return False

    def to_polyline(self):
        """ Returns a self-closing polyline. """
        return polyline(self.vertices)

    def to_shapely(self):
        """ Returns a Shapely Polygon instance. """
        try:
            if self.rank == 2:
                return geometry.Polygon([(v[0], v[1]) for v in self.vertices])
            elif self.rank == 3:
                return geometry.Polygon([(v[0], v[1], v[2]) for v in self.vertices])
        except NameError:
            raise Exception('Shapely module did not import\n')


def ray_intersection(pt, endpt1, endpt2, direction=0.0):
    """ Determines whether a ray intersects a line segment. If yes,
    returns the point of intersection. If no, return None. Input
    "points" should be tuples or similar. Input direction is in
    radians, and defines the ray path from pt.
    """
    m_ray = math.tan(direction)
    if endpt2[0] != endpt1[0]:
        m_lin = float(endpt2[1] - endpt1[1]) / float(endpt2[0] - endpt1[0])
        if m_ray == m_lin:      # Lines are parallel
            return
        else:
            x_int = ( (m_ray * pt[0] - m_lin * endpt1[0] - pt[1] + endpt1[1])
                / (m_ray - m_lin) )

        # Test that y_int is within segment and ray points toward segment
        if ( (x_int >= endpt1[0]) is not (x_int >= endpt2[0]) and
            (x_int-pt[0] > 0) is (math.cos(direction) > 0) ):
            y_int = ( (m_ray * m_lin * pt[0] - m_ray * m_lin * endpt1[0]
                + m_ray * endpt1[1] - m_lin * pt[1]) / (m_ray - m_lin) )
            return (x_int, y_int)
        else:
            return

    else:       # Line segment is vertical
        if direction % math.pi/2. == 0.0 and direction != 0.0:  # Lines are parallel
            return
        x_int = float(endpt1[0])
        y_int = (x_int - pt[0]) * m_ray + pt[1]
        # Test that y_int is within segment and ray points toward segment
        if ( (y_int >= endpt1[1]) is not (y_int >= endpt2[1]) and
            (x_int-pt[0] > 0) is (math.cos(direction) > 0) ):
            return (x_int, y_int)
        else:
            return



def pt_nearest(pt, endpt1, endpt2):
    """ Determines the point on a segment defined by tuples endpt1
    and endpt2 nearest to a point defined by tuple pt.
    Returns the a nested tuple of (point, distance)
    """
    dot2 = lambda v1,v2: float(v1[0]*v2[0] + v1[1]*v2[1])
    proj2 = lambda u,v: [dot2(u,v) / dot2(v,v) * e for e in v]
    dist = lambda u,v: math.sqrt((u[0]-v[0])**2. + (u[1]-v[1])**2.)

    u = (pt[0] - endpt1[0], pt[1] - endpt1[1])
    v = (endpt2[0] - endpt1[0], endpt2[1] - endpt1[1])
    u_on_v = proj2(u,v)
    u_int = (u_on_v[0] + endpt1[0], u_on_v[1] + endpt1[1])
    dist_u_int = dist(u_int, pt)

    # Determine whether u_int is inside the segment
    # Otherwise return the nearest endpoint
    if endpt1[0] == endpt2[0]:  # Segment is vertical
        if u_int[1] > max(endpt1[1], endpt2[1]):
            return (endpt1[1] > endpt2[1]
                    and (endpt1, dist(endpt1, pt))
                    or (endpt2, dist(endpt2, pt)))
        elif u_int[1] < min(endpt1[1], endpt2[1]):
            return (endpt1[1] < endpt2[1]
                    and (endpt1, dist(endpt1, pt))
                    or (endpt2, dist(endpt2, pt)))
        else:
            return (u_int, dist(u_int, pt))
    else:
        if u_int[0] > max(endpt1[0], endpt2[0]):
            return (endpt1[0] > endpt2[0]
                    and (endpt1, dist(endpt1, pt))
                    or (endpt2, dist(endpt2, pt)))
        elif u_int[0] < min(endpt1[0], endpt2[0]):
            return (endpt1[0] < endpt2[0]
                    and (endpt1, dist(endpt1, pt))
                    or (endpt2, dist(endpt2, pt)))
        else:
            return (u_int, dist(u_int, pt))


def distance(pntlist, angular_unit = "deg", space_unit = "km",
        method = "vicenty"):
    """ Computes the great circle distance between n point pairs on a
    sphere. Returns a list of length (n-1)

    [pntlist] contains a list of point objects

    [angular_unit] may be "deg" (default) or "rad".

    [space_unit] may be "km" (kilometers, default), "m" (meters), "mi"
    (miles), "ft" (feet), or "nm" (nautical miles).

    [method] may be "vicenty" (default) or "haversine". The Haversine
    method is roughly 20% faster, but may yield rounding errors when
    coordinates are antipodal.
    """

    radius = 6371.

    if angular_unit == "deg":
        xpts = [i.x * 3.14159 / 180. for i in pntlist]
        ypts = [i.y * 3.14159 / 180. for i in pntlist]
    elif angular_unit == "rad":
        xpts = [i.x for i in pntlist]
        ypts = [i.y for i in pntlist]
    else:
        raise Exception("Angular unit unrecognized")
        return None

    distances = []

    for i in xrange(len(pntlist)-1):

        x1 = xpts[i]
        x2 = xpts[i+1]
        y1 = ypts[i]
        y2 = ypts[i+1]
        dx = x2 - x1
        dy = y2 - y1
        if method == "haversine":
            try:
                distance = 2 * radius * math.asin(math.sqrt((math.sin(dy /
                    2.))**2 + math.cos(y1) * math.cos(y2) *
                    (math.sin(dx / 2.))**2))
            except Exception:
                traceback.print_exc()
        elif method == "vicenty":
            try:
                a = math.sqrt((math.cos(y2) * math.sin(dx))**2 +
                    (math.cos(y1) * math.sin(y2) - math.sin(y1) *
                    math.cos(y2) * math.cos(dx))**2)
                b = (math.sin(y1) * math.sin(y2) + math.cos(y1) *
                    math.cos(y2) * math.cos(dx))
                distance = radius * math.atan2(a, b)
            except ZeroDivisionError:
                raise Exception("Zero in denominator")
                return None
            except Exception:
                traceback.print_exc()
        else:
            raise Exception("Distance method unrecognized")
            return None

        distances.append(distance)

    if space_unit == "km": pass
    elif space_unit == "m": distances = [i * 1000. for i in distances]
    elif space_unit == "mi": distances = [i * 0.6213712 for i in distances]
    elif space_unit == "ft": distances = [i * 3280.840 for i in distances]
    elif space_unit == "nm": distances = [i * 0.5399568 for i in distances]
    else:
        print "Space unit unrecognized"
        return None

    return distances


def walk(start_pt, distance, bearing, azimuth=0.0, spherical=False):
    """ Returns the point reached when moving in a given direction for
    a given distance from a specified starting location.

        start_pt (point): starting location
        distance (float): distance to walk
        bearing (float): horizontal walk direction in radians
        azimuth (float): vertical walk direction in radians

        [NOT IMPLEMENTED]
        spherical (bool): use a spherical reference surface (globe)
    """
    if azimuth != 0.0:
        distxy = distance * math.sin(azimuth)
        dz = distance * math.cos(aximuth)
    else:
        distxy = distance
        dz = 0.0
    dx = distxy * math.sin(bearing)
    dy = distxy * math.cos(bearing)

    if start_pt.rank == 3:
        return point((start_pt.x+dx, start_pt.y+dy, start_pt.z+dz))
    elif start_pt.rank == 2:
        if azimuth != 0:
            sys.stderr.write("Warning: start_pt has rank 2 but azimuth is nonzero\n")
        return point((start_pt.x+dx, start_pt.y+dy))


def sortby(A, B):
    """ Sort a list A by the values in an ordered list B. """
    if len(A) == len(B): pass
    else: raise Exception("A and B must be of the same length")
    comb = zip(B,A)
    comb.sort()
    return [i[1] for i in comb]


def tighten(X, Z):
    """ Return a list of corrected measurements from observations of
    topography across a cross-section. The inputs are equal length
    lists of observed distance and elevation.

    Usage scenario: While surveying transects using a tape, the tape
    is anchored to the topographical surface, rather than directly
    between same-height endpoints.
    """
    if len(X) != len(Z):
        raise Exception('Observation vectors must have equal length')

    DZ = [z2-z1 for z2,z1 in zip(Z[1:], Z[:-1])]
    DX = [x2-x1 for x2,x1 in zip(X[1:], X[:-1])]

    DXt = [math.sqrt(x*x-z*z) for x,z in zip(DX, DZ)]

    Xt = map(lambda i: sum(DXt[:i]) + X[0], range(len(DX)))

    return zip(Xt, Z)